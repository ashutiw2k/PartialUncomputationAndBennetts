

import collections
import copy
from typing import List
import qiskit
import rustworkx
from tqdm import tqdm
import string

from .constants import StringConstants
from .graphhelper import CGNode, breakdown_qubit

INPUT = StringConstants.INPUT.value
ANCILLA = StringConstants.ANCILLA.value
OUTPUT = StringConstants.OUTPUT.value

INIT = StringConstants.INIT.value
COMP = StringConstants.COMP.value
UNCOMP = StringConstants.UNCOMP.value

TARGET = StringConstants.TARGET.value
CONTROL = StringConstants.CONTROL.value
ANTIDEP = StringConstants.ANTIDEP.value


def get_computation_graph(circuit: qiskit.circuit.QuantumCircuit, ancillas: List, outputs: List=[]):
    circuit_graph = rustworkx.PyDiGraph(multigraph=False)
    last_node_index = {}
    # Add the initial qubits

    # ANCILLA_START = ancilla_start

    circuit_qubits = circuit.qubits
    circuit_data = circuit.data

    for qubit in circuit_qubits:
        qubit_dict = breakdown_qubit(qubit)
        
        if outputs:
            qubit_type = ANCILLA if qubit_dict['label'] in ancillas else (OUTPUT if qubit_dict['label'] in outputs else INPUT)
                
        else: 
            qubit_type = ANCILLA if qubit_dict['label'] in ancillas else INPUT
        
                
        init_node = CGNode(qubit_dict, qubit_type=qubit_type, node_type=INIT)
        index = circuit_graph.add_node(init_node)
        circuit_graph.get_node_data(index).set_index(index)
        circuit_graph.get_node_data(index).set_nodenum(0)
        last_node_index[init_node.label] = index

    # print(circuit_graph.nodes())
    # for node in circuit_graph.nodes():
    #     print(node)
    # print(last_node_index)

    # Adding Computation Gates
    output_qubit_counter = 0
    for circ_inst in tqdm(circuit_data, desc=f'Adding Nodes for Circuit'):
        opname = circ_inst.operation.name
        qubit_dict_all = []
        for qubit in circ_inst.qubits:
            qubit_dict_all.append(breakdown_qubit(qubit))
        # print(qubit_dict_all)
        # target_qubit_dict = qubit_dict_all[-1]
        # target_label = target_qubit_dict['name'] + str(target_qubit_dict['wire'])
        # target_index = last_node_index[target_label]
        qubit_indicies = [last_node_index[qubit_dict['label']] for qubit_dict in qubit_dict_all]
        # print(qubit_indicies)
        prev_node_index = qubit_indicies.pop()
        # print(prev_node_index)
        # Adding the node
        
        if outputs:
            qubit_type = ANCILLA if qubit_dict_all[-1]['label'] in ancillas else (OUTPUT if qubit_dict_all[-1]['label'] in outputs else INPUT)         
        else: 
            qubit_type = ANCILLA if qubit_dict_all[-1]['label'] in ancillas else INPUT

        

        # For bennetts uncomp, once all the output qubit operations are added then 
        # the remaining gates are uncomp gates. 
        if outputs and output_qubit_counter == len(outputs):
            node_type = UNCOMP
        else:
            node_type = COMP

        if qubit_type == OUTPUT:
            output_qubit_counter += 1
        
        opnode = CGNode(qubit_dict_all[-1], qubit_type=qubit_type, node_type=node_type, opname=opname)
        
        params = circ_inst.operation.params
        if len(params) == 1:
            opnode.theta = params[0]

        opnode_index = circuit_graph.add_child(prev_node_index, opnode, TARGET)
        circuit_graph.get_node_data(opnode_index).set_index(opnode_index)
        circuit_graph.get_node_data(opnode_index).set_nodenum(
            circuit_graph.get_node_data(prev_node_index).get_nodenum() + (1 if node_type is COMP else -1)
        )
        last_node_index[opnode.label] = opnode_index

        # Adding the control edges and Antidep between controls
        for qubit_index in qubit_indicies:
            circuit_graph.add_edge(qubit_index, opnode_index, CONTROL)        
            
            controls_adj = circuit_graph.adj_direction(qubit_index, False)
            try:
                controls_target_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == TARGET and not circuit_graph.has_edge(x[0], opnode_index), list(controls_adj.items())))))
            except IndexError:
                controls_target_idx = []

            for idx in controls_target_idx:
                circuit_graph.add_edge(opnode_index, idx, ANTIDEP)

        # Adding AntiDep Edges (Opnode to OTHER controlled nodes)
        prev_node_adj = circuit_graph.adj_direction(prev_node_index, False)
        # print(prev_node_adj)
        try:
            prev_node_controlled_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == CONTROL and not circuit_graph.has_edge(x[0], opnode_index), list(prev_node_adj.items())))))
        except IndexError:
            prev_node_controlled_idx = []

        for idx in prev_node_controlled_idx:
            circuit_graph.add_edge(idx, opnode_index, ANTIDEP)
            

        # print(circuit_graph.adj(opnode_index))

        # print('----------------------------------------')
        


    return circuit_graph


def get_uncomp_circuit(circuit_graph: rustworkx.PyDiGraph):
    
    sorted_circuit_graph = rustworkx.topological_sort(copy.deepcopy(circuit_graph))
    # print(sorted_circuit_graph)

    init_nodes = list(filter(lambda x: x.node_type == INIT, circuit_graph.nodes()))
    init_nodes_qubits = collections.Counter([x.qubit_name for x in init_nodes])
    init_node_labels = [x.label for x in init_nodes]

    qubits = [qiskit.QuantumRegister(size=x[1], name=x[0]) for x in init_nodes_qubits.items()]

    # print(init_nodes_qubits)
    # print(init_node_labels)

    new_uncomp_circuit = qiskit.QuantumCircuit(*qubits)


    # uncomp_circuit = qiskit.QuantumCircuit(len(list(filter(lambda x: x.node_type == INIT, circuit_graph.nodes()))))

    for idx in tqdm(sorted_circuit_graph, desc=f'Building uncomp circuit from circuit graph'):
        # print(circuit_graph.nodes()[idx])
        node = circuit_graph.get_node_data(idx) 
        # print(node)
        
        node_incoming_edges = circuit_graph.adj_direction(idx, True)
        
        try:
            node_prev_idx = list(filter(lambda x: x[1] == TARGET, list(node_incoming_edges.items()))).pop()[0]
        except IndexError:
            node_prev_idx = None

        try:
            node_controls_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == CONTROL, list(node_incoming_edges.items())))))
        except IndexError:
            node_controls_idx = []

        # node_controls = circuit_graph.find_successors_by_edge(idx, lambda x:x==CONTROL)
        # print(node_prev_idx)
        # print(node_controls_idx)
        # print('------------------------------------------------')
        if node_prev_idx is None:
            continue
        prev_node = circuit_graph.get_node_data(node_prev_idx)
        prev_node_wire = init_node_labels.index(prev_node.label)
        control_nodes = [circuit_graph.get_node_data(idx) for idx in node_controls_idx]
        control_nodes_wires = [init_node_labels.index(node.label) for node in control_nodes]
        opname = node.opname
        if opname == 'mcx':
            controls = [control_nodes_wires[i] for i in range(len(control_nodes_wires))]
            new_uncomp_circuit.mcx(controls, prev_node_wire)
        elif opname == 'ccx':
            assert len(control_nodes_wires) == 2
            new_uncomp_circuit.ccx(control_nodes_wires[0], control_nodes_wires[1], prev_node_wire)
        elif opname == 'cx':
            assert len(control_nodes_wires) == 1
            new_uncomp_circuit.cx(control_nodes_wires[0], prev_node_wire)
        elif opname == 'cz':
            assert len(control_nodes_wires) == 1
            new_uncomp_circuit.cz(control_nodes_wires[0], prev_node_wire)
        elif opname == 'x':
            assert len(control_nodes_wires) == 0
            new_uncomp_circuit.x(prev_node_wire)
        elif opname == 'z':
            assert len(control_nodes_wires) == 0
            new_uncomp_circuit.z(prev_node_wire)
        elif opname == 'h':
            assert len(control_nodes_wires) == 0
            new_uncomp_circuit.h(prev_node_wire)
        
        elif opname == 'rx':
            assert len(control_nodes_wires) == 0
            new_uncomp_circuit.rx(node.theta, prev_node_wire)
        elif opname == 'ry':
            assert len(control_nodes_wires) == 0
            new_uncomp_circuit.ry(node.theta, prev_node_wire)
        elif opname == 'rz':
            assert len(control_nodes_wires) == 0
            new_uncomp_circuit.rz(node.theta, prev_node_wire)

        elif opname =='barrier':
            # assert len(control_nodes_wires) == 0
            new_uncomp_circuit.barrier()

        else:
            print(f'Operation {opname} DNE in QC Builder')


    return new_uncomp_circuit
