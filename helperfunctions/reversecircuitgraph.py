import collections
import copy
from itertools import chain, combinations
import time
from typing import Dict, List
import logging
from qiskit import QuantumCircuit
import rustworkx
from tqdm import tqdm

from .uncompfunctions import add_uncomputation_step
from .constants import StringConstants, ListConstants
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

NON_QFREE = ListConstants.NON_QFREE.value

# Logger for overview
logger = logging.getLogger(__name__)

 
def reverse_all_operations(circuit_graph : rustworkx.PyDiGraph):
    uncomp_circuit_graph = copy.deepcopy(circuit_graph)
    nodelist = list(rustworkx.topological_sort(circuit_graph))
    nodelist.reverse()
    for id in nodelist:
        node = circuit_graph.get_node_data(id)
        if not node.qubit_type is OUTPUT and node.node_type is COMP:
            cycle = add_uncomputation_step(uncomp_circuit_graph, id)
            if cycle:
                print(f'Cycle found: {cycle}')
    
    return uncomp_circuit_graph

def uncomp_all_operations_using_circuitgraph(circuit_graph : rustworkx.PyDiGraph):
    uncomp_circuit_graph = copy.deepcopy(circuit_graph)
    nodelist = list(rustworkx.topological_sort(circuit_graph))
    nodelist.reverse()
    for id in nodelist:
        node = circuit_graph.get_node_data(id)
        if not node.qubit_type is OUTPUT and node.node_type is COMP and not node.is_uncomputed:
            cycle = add_uncomputation_step(uncomp_circuit_graph, id)
            if cycle:
                print(f'Cycle found: {cycle}')
    
    return uncomp_circuit_graph


def add_uncomp_input_node(node_index: int, circuit_graph:rustworkx.PyDiGraph):
    '''
    Algorithm for adding uncomp for an input qubit node/gate. 
    1.  Get node 'c' to uncompute. Get node_num 'i' of this node. 
    2.  If node has a target edge and uncomp node of qubit with node_num 'i' 
        does not exist, then recursively uncompute node with node_num 'i'
    3.  At this point, uncomp node of node_num 'i' should exist.
    4.  Create new uncomp node 'c*' with node_num 'i-1' for the input qubit. 
    5.  Restructing edges:
        5.1 Any control edges to UNCOMP nodes from c will be redirected to c*
        5.2 Anti dep edges from any UNCOMP node to node 'i' where node 'c' 
            is the control can be removed
    '''

    comp_node = circuit_graph.get_node_data(node_index)
    assert comp_node.node_type is COMP, f"Node is not {COMP} node." 
    assert comp_node.qubit_type is INPUT, f"Node is not {INPUT} node."


    node_num = comp_node.get_nodenum()
    qubit = comp_node.label
    # print(node_num)

    incoming_edges = circuit_graph.adj_direction(node_index, True)
    outgoing_edges = circuit_graph.adj_direction(node_index, False)

    # 2.  If node has a target edge and uncomp node of qubit with node_num 'i' 
    #     does not exist, then recursively uncompute node with node_num 'i'

    target = [x[0] for x in outgoing_edges.items() if x[1] is TARGET]
    uncomped = [node for node in circuit_graph.nodes() \
                if node.label == qubit and node.get_nodenum() == node_num and node.node_type is UNCOMP]
    
    # print(target)
    # print(uncomped)

    if  len(target) and not len(uncomped):

        assert len(target) == 1, f'Target List has more than 1 node, this is wrong.'
        to_be_uncomped = target[0]

        print(f'''{comp_node.simple_graph_label()} can not be uncomputed yet, as the successive nodenum is yet to be uncomputed.
              Uncomputing {circuit_graph.get_node_data(to_be_uncomped).simple_graph_label()}.''')
        
        circuit_graph = add_uncomp_input_node(to_be_uncomped, circuit_graph)
    
    # At this point, either the input qubit node should have no target edge, 
    # or uncomp node with node num 'i' exists. 

    print(f'Now uncomputing {node_index}:{comp_node.simple_graph_label()}')
    uncomp_node_idx, has_cycle = add_uncomputation_step(circuit_graph, node_index, return_uncomp_node=True)
          
    # uncomp_node = circuit_graph.get_node_data(uncomp_node_idx)

    # print(uncomp_node)

    # Step 5
    prev_node = [x for x,y in incoming_edges.items() if y == TARGET]
    
    assert len(prev_node) == 1
    c_node = prev_node[0]
    c_node_outgoing_edges = circuit_graph.adj_direction(c_node, False)


    # 5.1 Any control edges to UNCOMP nodes from c will be redirected to c*
    # 5.2 Anti dep edges from any UNCOMP node to node 'i' where node 'c' is the control can be removed

    uncomp_nodes_controlled = [x for x,y in c_node_outgoing_edges.items() \
                               if y == CONTROL and circuit_graph.get_node_data(x).node_type == UNCOMP]
    
    # edges_to_remove = [x for x,y in incoming_edges.items()\
    #                  if y == ANTIDEP and circuit_graph.get_node_data(x).node_type == UNCOMP]
    
    # The node 'n' will be common, as the anti dep edge from uncomp node 'n' to 'c' 
    # will exist iff a control edge exists from prev node to 'n'
    for n in uncomp_nodes_controlled:
        circuit_graph.remove_edge(c_node, n)
        circuit_graph.add_edge(uncomp_node_idx, n, CONTROL)
        circuit_graph.remove_edge(n, node_index)

     
    # # print(old_anti_dep)
    # for n in edges_to_remove:
    #     circuit_graph.remove_edge(n,node_index)

    has_cycle = rustworkx.digraph_find_cycle(circuit_graph)
    if has_cycle:
        print(f'Added Uncomp for {comp_node.simple_graph_label()} but CG has cycles')
    else:
        print(f'Cycles from CG removed when added uncomp for {comp_node.simple_graph_label()}!')


    return circuit_graph


def remove_uncomp_input_node(node_index: int, circuit_graph:rustworkx.PyDiGraph):
    '''
    Algorithm for removing uncomp for an input qubit node. 
    1.  
    '''

    node = circuit_graph.get_node_data(node_index)


    pass

# def reverse_input_qubits(circuit_graph:rustworkx.PyDiGraph):
#     input_init_nodes = [node for node in circuit_graph.nodes() if node.node_type == INIT and node.qubit_type is not ANCILLA]
#     input_qubits = [node.label for node in input_init_nodes]
#     input_qubits_counter = collections.Counter(input_qubits)
#     input_qubits_counter.subtract(input_qubits)
#     input_target_nodes = {}
#     for node in input_init_nodes:
#         qubit = node.label
#         targets = []
#         target_node = circuit_graph.find_adjacent_node_by_edge(node.get_index(), lambda x : x == TARGET)

#         while target_node:
#             targets.append(target_node)
#             try:
#                 target_node = circuit_graph.find_adjacent_node_by_edge(target_node.get_index(), lambda x : x == TARGET)
#             except:
#                 target_node = None

#         input_target_nodes.update({qubit:targets})

#     print(input_target_nodes)

#     pass


def greedy_metric_num_uncomp_antidep(node_index:int, circuit_graph:rustworkx.PyDiGraph):
    '''
    The greedy metric here is most number of anti dependency edges from ancilla uncomp nodes 
    that come into the node.
    '''
    return len([x for x,y in circuit_graph.adj_direction(node_index, True).items() 
                        if y is ANTIDEP and circuit_graph.get_node_data(x).qubit_type is ANCILLA 
                        and circuit_graph.get_node_data(x).node_type is UNCOMP])

def greedily_select_input_node(circuit_graph:rustworkx.PyDiGraph):
    '''
    This method determines the best input qubit to uncompute by choosing the input qubit
    with the specified greedy metric. 
    '''
    best_index = 0
    for idx in circuit_graph.node_indices():
        node = circuit_graph.get_node_data(idx)
        if node.qubit_type is INPUT and node.node_type is COMP and not node.is_uncomputed:
            best_index = idx
            break

    for idx in circuit_graph.node_indices():
        node = circuit_graph.get_node_data(idx)
        
        if  node.qubit_type is INPUT and node.node_type is COMP and not node.is_uncomputed \
            and greedy_metric_num_uncomp_antidep(idx, circuit_graph) > greedy_metric_num_uncomp_antidep(best_index, circuit_graph) :
            
            best_index = idx

    return best_index

def uncompute_input_nodes_greedy(circuit_graph:rustworkx.PyDiGraph):
    while rustworkx.digraph_find_cycle(circuit_graph):
        best_node_to_uncompute = greedily_select_input_node(circuit_graph)
        print(f'Best Node to uncompute is {best_node_to_uncompute} : {circuit_graph.get_node_data(best_node_to_uncompute).simple_graph_label()}')
        add_uncomp_input_node(best_node_to_uncompute, circuit_graph)
    
    return circuit_graph

def get_bennetts_reduced_uncomp_without_reordering(circuit: QuantumCircuit, ancillas: List, num_gates:int):
    instructions = list(circuit.data[:num_gates])

    ctr = 0
    for ins in instructions:
        anc = [1 for q in ins.qubits if breakdown_qubit(q)['label'] in ancillas]
        if len(anc) == 0:
            ctr += 1
        else:
            break
    print(f'The first {ctr} gates are between input qubits, they can be ignored in bennetts uncomp.')
    
    valid_instructions = instructions[ctr:]
    valid_instructions.reverse()

    benentts_uncomp_circuit = circuit.copy()
    for ins in valid_instructions:
        benentts_uncomp_circuit.append(ins)

    return benentts_uncomp_circuit
    

def remove_nodes_not_in_bennetts(all_uncomp_graph:rustworkx.PyDiGraph, bennetts_uncomp_graph:rustworkx.PyDiGraph, matcher_func):
    # Pre-compute all potential matches for faster lookup
    nodes_to_remove = []
    new_uncomp_graph = all_uncomp_graph.copy()

    # Optional: If nodes have attributes that can be hashed for quicker comparison
    # Create a set or dictionary for faster lookups
    # This assumes node objects have comparable attributes
    
    # For each node in the first graph
    for node in all_uncomp_graph.nodes():
        # Use any() for short-circuit evaluation
        if not any(matcher_func(node, b_node) for b_node in bennetts_uncomp_graph.nodes()):
            nodes_to_remove.append(node.index)
    
    # Remove nodes in reverse order to avoid index shifting
    for node_index in sorted(nodes_to_remove, reverse=True):
        new_uncomp_graph.remove_node(node_index)

    return new_uncomp_graph
    
