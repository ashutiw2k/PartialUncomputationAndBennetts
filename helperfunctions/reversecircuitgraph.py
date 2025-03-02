import collections
import copy
from itertools import chain, combinations
import time
from typing import Dict, List
import logging
import rustworkx
from tqdm import tqdm

from .uncompfunctions import add_uncomputation_step
from .constants import StringConstants, ListConstants
from .graphhelper import CGNode

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

def uncomp_operations(circuit_graph : rustworkx.PyDiGraph):
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
    Algorithm for adding uncomp for an input qubit node. 
    1.  Get node 'c' to uncompute. Get node_num 'i' of this node. 
    2.  If uncomp node of qubit with node_num 'i' does not exist, 
        and node has a target edge, then recursively uncompute node 
        with node_num 'i'
    3.  At this point, uncomp node of node_num 'i' should exist.
    4.  Create new uncomp node 'c*' with node_num 'i-1' for the input qubit. 
    5.  Restructing edges:
        5.1 Any control edges to UNCOMP nodes from c will be redirected to c*
        5.2 Anti dep edges from any UNCOMP node to node 'i+1' where node 'c' 
            is the control can be removed
    '''

    node = circuit_graph.get_node_data(node_index)
    assert node.node_type is not UNCOMP and node.qubit_type is INPUT

    node_num = node.get_nodenum()

    incoming_edges = circuit_graph.adj_direction(node_index, True)
    outgoing_edges = circuit_graph.adj_direction(node_index, False)

    # if 


    # has_target_edge = 


    pass

def remove_uncomp_input_node(node_index: int, circuit_graph:rustworkx.PyDiGraph):
    '''
    Algorithm for removing uncomp for an input qubit node. 
    1.  
    '''

    node = circuit_graph.get_node_data(node_index)


    pass

def reverse_input_qubits(circuit_graph:rustworkx.PyDiGraph):
    input_init_nodes = [node for node in circuit_graph.nodes() if node.node_type == INIT and node.qubit_type is not ANCILLA]
    input_qubits = [node.label for node in input_init_nodes]
    input_qubits_counter = collections.Counter(input_qubits)
    input_qubits_counter.subtract(input_qubits)
    input_target_nodes = {}
    for node in input_init_nodes:
        qubit = node.label
        targets = []
        target_node = circuit_graph.find_adjacent_node_by_edge(node.get_index(), lambda x : x == TARGET)

        while target_node:
            targets.append(target_node)
            try:
                target_node = circuit_graph.find_adjacent_node_by_edge(target_node.get_index(), lambda x : x == TARGET)
            except:
                target_node = None

        input_target_nodes.update({qubit:targets})

    print(input_target_nodes)

    pass