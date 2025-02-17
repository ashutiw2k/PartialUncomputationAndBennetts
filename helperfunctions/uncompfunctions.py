import collections
import copy
from itertools import chain, combinations
import time
from typing import Dict, List
import logging
import rustworkx
from tqdm import tqdm

from .constants import StringConstants, ListConstants
from .graphhelper import CGNode


ANCILLA = StringConstants.ANCILLA.value

INIT = StringConstants.INIT.value
COMP = StringConstants.COMP.value
UNCOMP = StringConstants.UNCOMP.value

TARGET = StringConstants.TARGET.value
CONTROL = StringConstants.CONTROL.value
ANTIDEP = StringConstants.ANTIDEP.value

NON_QFREE = ListConstants.NON_QFREE.value

# Logger for overview
logger = logging.getLogger(__name__)

# This method is to implement Lines 10,11 of the PLDI algorithm
# If to uncomp node, ctrl* exists, replace ctrl with ctrl*
def get_uncomp_node_index(circuit_graph: rustworkx.PyDiGraph, node_index):
    for node in circuit_graph.nodes():
        if node.node_type is UNCOMP \
            and node.label == circuit_graph.get_node_data(node_index).label \
            and node.get_nodenum() == circuit_graph.get_node_data(node_index).get_nodenum():
            
            return node.get_index()
    return node_index

# This method is to reverse Lines 10,11 of the PLDI algorithm
# If we remove uncomp node, and node acts as a control, replace with ctrl* with ctrl
def get_comp_node_index(circuit_graph: rustworkx.PyDiGraph, node_index):
    for node in circuit_graph.nodes():
        if node.node_type is not UNCOMP \
            and node.label == circuit_graph.get_node_data(node_index).label \
            and node.get_nodenum() == circuit_graph.get_node_data(node_index).get_nodenum():

            return node.get_index()
    return node_index


def add_uncomputation_step(circuit_graph: rustworkx.PyDiGraph, idx):
    '''
    PLDI's UncompStep implementation
    '''
    # Get node data
    node = circuit_graph.get_node_data(idx)

    # Get all the edges coming into the node
    node_adj = circuit_graph.adj_direction(idx, True)

    # Check, may need to modify?
    assert node.opname not in NON_QFREE

    # Filter all the incoming edges to get the control edges controlling the node.
    try:
        node_controls_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == CONTROL, list(node_adj.items())))))
    except IndexError:
        node_controls_idx = []

    # print(node_controls_idx)

    # If any controls are ancilla and have their uncomp node ready, replace control with uncomp control
    node_controls_idx_uncomp = list(map(lambda x: get_uncomp_node_index(circuit_graph, x), node_controls_idx))
    # print(node_controls_idx_uncomp)

    # Get the previous node. a[n] if first uncomp else a*[n-1]
    prev_node_index = node.get_index()
    for n in circuit_graph.nodes():
        if n.label == node.label and n.node_type is UNCOMP and n.get_nodenum() == node.get_nodenum():
            prev_node_index = n.get_index()

    # print(prev_node_index)

    # Build and add the uncomp node to the circuit graph
    uncomp_node = CGNode(node.qubit_dict, qubit_type=node.qubit_type, node_type=UNCOMP, opname=node.opname)
    # uncomp_node_index = circuit_graph.add_node(uncomp_node)
    uncomp_node_index = circuit_graph.add_child(prev_node_index, uncomp_node, TARGET)
    circuit_graph.get_node_data(uncomp_node_index).set_index(uncomp_node_index)
    circuit_graph.get_node_data(uncomp_node_index).set_nodenum(
        circuit_graph.get_node_data(node.get_index()).get_nodenum() - 1
    )

    # Adding Control Edges and the antidep of control edges. 
    # a*[n-1] - -> v | c --> v (c in ctrls of a*[n-1])
    for control_idx in node_controls_idx_uncomp:
        circuit_graph.add_edge(control_idx, uncomp_node_index, CONTROL)

        controls_adj = circuit_graph.adj_direction(control_idx, False)
        try:
            controls_target_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == TARGET and not circuit_graph.has_edge(x[0], uncomp_node_index), 
                                                                       list(controls_adj.items())))))
        except IndexError:
            controls_target_idx = []

        for idx in controls_target_idx:
            circuit_graph.add_edge(uncomp_node_index, idx, ANTIDEP)

    # Add anti dependency edges between nodes controlled by of node and new uncomp node
    # v - -> a*[n-1] | a*n o--> v (any v in G)
    prev_node_adj = circuit_graph.adj_direction(prev_node_index, False)
    # print(prev_node_adj)
    try:
        prev_node_controlled_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == CONTROL and not circuit_graph.has_edge(x[0], uncomp_node_index), list(prev_node_adj.items())))))
    except IndexError:
        prev_node_controlled_idx = []

    for idx in prev_node_controlled_idx:
        circuit_graph.add_edge(idx, uncomp_node_index, ANTIDEP)


    # print(uncomp_node)

    # print('----------------------------------------')


    return rustworkx.digraph_find_cycle(circuit_graph)

def add_uncomputation(circuit_graph: rustworkx.PyDiGraph, ancillas:List[str], allow_cycle=False):
    '''
    PLDI's Uncomp implementation
    '''
    uncomp_circuit_graph = copy.deepcopy(circuit_graph)
    graph_nodes_reverse = list(rustworkx.topological_sort(copy.deepcopy(circuit_graph)))
    # Reverse the graph nodes, to add uncomp. 
    graph_nodes_reverse.reverse()
    # print(graph_nodes_reverse)
    for idx in graph_nodes_reverse:
        if circuit_graph.get_node_data(idx).label in ancillas and circuit_graph.get_node_data(idx).node_type is COMP:
            cycle = add_uncomputation_step(uncomp_circuit_graph, idx)

            if not allow_cycle and len(cycle) > 0:
                # print(f'Adding Uncomp node for {uncomp_circuit_graph.get_node_data(idx).graph_label()} creates a cycle of nodes => {cycle}:')
                # for id in cycle:
                #     print(uncomp_circuit_graph.get_node_data(id[0]).graph_label(), uncomp_circuit_graph.get_node_data(id[1]).graph_label(), sep=' --> ')

                return uncomp_circuit_graph, True

    return uncomp_circuit_graph, False

def exhaustive_uncomputation(circuit_graph: rustworkx.PyDiGraph, ancillas:List[str], return_uncomputed_ancillas=False):
    largest_set = exhaustive_uncomputation_adding(circuit_graph, ancillas)
    uncomp_graph, has_cycle = add_uncomputation(circuit_graph, largest_set)
    if has_cycle:
        raise ValueError(f'Largest Set of Ancillas {largest_set} still causes cycles in uncomp graph')
    if return_uncomputed_ancillas:
        return uncomp_graph, largest_set
    else:
        return uncomp_graph  

def exhaustive_uncomputation_adding(circuit_graph: rustworkx.PyDiGraph, ancillas:List[str]):
    '''
    Exhaustively iterate over adding uncomputation for all possible ancillas
    '''
    
    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    ancillas_power_set = chain.from_iterable(combinations(ancillas, r) for r in range(len(ancillas)+1))
    largest_uncomputable = ()
    for ancilla_set in tqdm(ancillas_power_set, desc='Checking Out Exhaustive Uncomp for All Ancillas'):
        # uncomp_circuit_graph = copy.deepcopy(circuit_graph)
        # print(f'Adding Uncomputation for ancilla set {ancilla_set}')
        # logger.info(f'Adding Uncomputation for ancilla set {ancilla_set}')
        uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, list(ancilla_set))
        
        if not has_cycle and len(ancilla_set) > len(largest_uncomputable):
            largest_uncomputable = ancilla_set

    return largest_uncomputable

def exhaustive_uncomputation_adding_reverse(circuit_graph: rustworkx.PyDiGraph, ancillas:List[str]):
    '''
    Exhaustively iterate over adding uncomputation for all possible ancillas
    '''
    
    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    ancillas_power_set = list(chain.from_iterable(combinations(ancillas, r) for r in range(len(ancillas)+1)))
    # ancillas_power_set = 
    ancillas_power_set.reverse()
    # print(ancillas_power_set)

    largest_uncomputable = ()
    # ctr = 0
    for ancilla_set in tqdm(ancillas_power_set, desc='Checking Out Exhaustive Uncomp for All Ancillas'):
        uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, list(ancilla_set))
        
        if not has_cycle: 
            if len(ancilla_set) < len(largest_uncomputable):
                break
            largest_uncomputable = ancilla_set

    # print(largest_uncomputable)
    return largest_uncomputable
    
# Method to remove an uncomputation node and restructure the edges
def remove_uncomputation_step(uncomp_circuit_graph: rustworkx.PyDiGraph, idx):
    comp_node_index = get_comp_node_index(uncomp_circuit_graph, idx)

    adj_nodes = uncomp_circuit_graph.adj_direction(idx, False) # Get all outbound edges
    # print(adj_nodes)

    try:
        controlled_idx = list(map(lambda x: x[0], list(filter(lambda x: x[1] == CONTROL, list(adj_nodes.items())))))
    except IndexError:
        controlled_idx = []

    # print(controlled_idx)

    uncomp_circuit_graph.remove_node(idx)
    
    # Add the control edges from equivalent comp node and new anti dependency edges
    for idx in controlled_idx:
        uncomp_circuit_graph.add_edge(comp_node_index, idx, CONTROL)
        
        adj_edges_leaving = uncomp_circuit_graph.adj_direction(comp_node_index, False)
        next_node_idx = list(filter(lambda x: adj_edges_leaving[x] is TARGET, adj_edges_leaving.keys()))
            # list(map(lambda x: x[0], list(filter(lambda x: x[1] == TARGET and not uncomp_circuit_graph.has_edge(x[0], idx), list(adj_edges_leaving.items())))))
        if len(next_node_idx) > 1:
            raise ValueError.add_note(f'searching for targets returned more than one value : {next_node_idx}') 
    
        uncomp_circuit_graph.add_edge(idx, next_node_idx[0], ANTIDEP)

# Remove all uncomputation nodes for specified set of ancilla qubits 
def remove_uncomputation_full(uncomp_circuit_graph:rustworkx.PyDiGraph, ancillas: List[str]):
    # circuit_graph = copy.deepcopy(uncomp_circuit_graph)
    graph_nodes_reverse = uncomp_circuit_graph.nodes()
    graph_nodes_reverse.reverse()
    # print(graph_nodes_reverse)
    for node in graph_nodes_reverse:
        if node.label in ancillas and node.node_type is UNCOMP:
            remove_uncomputation_step(uncomp_circuit_graph, node.index)

    
    return uncomp_circuit_graph

# Exhaustive Uncomp implementation by removing uncomputation for subset of ancilla
def exhaustive_uncomputation_removing(circuit_graph: rustworkx.PyDiGraph, ancillas: List[str]):
    
    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    ancillas_power_set = chain.from_iterable(combinations(ancillas, r) for r in range(len(ancillas)+1))
    smallest_removable = ancillas
    
    uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, ancillas, allow_cycle=True)

    # if not has_cycle:
    #     return ancillas

    for ancilla_set in ancillas_power_set:
        reduced_uncomp_circuit_graph = remove_uncomputation_full(uncomp_circuit_graph, ancilla_set)
        cycle = rustworkx.digraph_find_cycle(reduced_uncomp_circuit_graph)

        if len(cycle) == 0 and len(ancilla_set) < len(smallest_removable):
            smallest_removable = ancilla_set


    return smallest_removable

# Greedily remove uncomputation - ALL UNCOMP NODES FOR VALID ANCILLA    
def greedy_uncomputation_full_weak(circuit_graph: rustworkx.PyDiGraph, ancillas):
    
    start_time = time.time_ns()
    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, ancillas, allow_cycle=True)
    logger.info(f'Time to build Greedy Uncomp Circuit Graph with cycles took {time.time_ns()-start_time} ns')
    start_time = time.time_ns()

    all_node_indicies = uncomp_circuit_graph.node_indices()
    # all_node_indicies
    for idx in all_node_indicies:
        if idx not in uncomp_circuit_graph.node_indices():
            continue
        
        node = uncomp_circuit_graph.get_node_data(idx)
        if not node.node_type == UNCOMP:
            continue

        if rustworkx.digraph_find_cycle(uncomp_circuit_graph, idx):
            uncomp_circuit_graph = remove_uncomputation_full(uncomp_circuit_graph, [node.label])

    return uncomp_circuit_graph



# Greedily remove uncomputation - ALL UNCOMP NODES FOR VALID ANCILLA    
def greedy_uncomputation_full(circuit_graph: rustworkx.PyDiGraph, ancillas:List[str], max_cycles:int=10**5, return_uncomputed_ancillas=False):
    
    start_time = time.time_ns()
    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, ancillas, allow_cycle=True)
    # logger.info(f'Time to build Greedy Uncomp Circuit Graph with cycles took {time.time_ns()-start_time} ns')
    uncomp_ancillas_list = copy.deepcopy(ancillas)
    # start_time = time.time_ns()

    cycle_check = rustworkx.digraph_find_cycle(uncomp_circuit_graph)
    # logger.info(f'Time to check for cycle in Greedy Uncomp Circuit Graph took {time.time_ns()-start_time} ns')
    # start_time = time.time_ns()
    
    while len(cycle_check) > 0:
        uncomp_cycle_counter = collections.Counter({i:0 for i in ancillas})
        # comp_cycle_counter = collections.Counter({i:0 for i in range(num_qubit+num_ancilla)})

        # Inbuilt Johnson's algorithm to find all simple cycles
        simple_cycles = rustworkx.simple_cycles(uncomp_circuit_graph)
        # logger.info(f'Time to get all simple cycles using Johnsons in Greedy Uncomp Circuit Graph took {time.time_ns()-start_time} ns')
        # start_time = time.time_ns()
        
        # Max iterations to run the loop for, as number of cycles can 
        # easily cross 1B (and take >1day to successively parse through)
        # max_cycles = 10**5
        cycle_counter = 0
        for cycle in tqdm(simple_cycles, desc=f'Iterating over all cycles in graph', total=max_cycles):
            # print(cycle)
            # For each node in cycle, update the counter based on whether it's an uncomp node or comp node
            for idx in cycle:
                node = uncomp_circuit_graph.get_node_data(idx)
                if node.qubit_type is ANCILLA: 
                    if node.node_type is UNCOMP:
                        uncomp_cycle_counter[node.label] +=1
                    # else:
                    #     comp_cycle_counter[node.qubit_wire] +=1
        
            if cycle_counter > max_cycles:
                break
            
            cycle_counter+=1

        # logger.info(f'There are a total of {len(list(simple_cycles))} in the graph, and a total of {sum([len(x) for x in simple_cycles])} labels to check')
        # print(f'There are a total of {len(list(simple_cycles))} simple cycles in the circuit graph.')
        # logger.info(f'There are a total of {len(List(simple_cycles))} simple cycles in the circuit graph.')

        # uncomp_cycle_labels = [uncomp_circuit_graph.get_node_data(idx).label for cycle in simple_cycles for idx in cycle if uncomp_circuit_graph.get_node_data(idx).node_type is UNCOMP]
        # uncomp_cycle_counter = collections.Counter(uncomp_cycle_labels)

        # logger.info(f'Time to get ancilla qubits with most cycles in Greedy Uncomp Circuit Graph took {time.time_ns()-start_time} ns')
        # start_time = time.time_ns()

        # Debugging warning, can be ignored as cycles can be introduced with the comp nodes 
        # AFTER adding uncomputation, which should be removed after greedy procedure
        # if comp_cycle_counter.total() > 0:
        #     print(f'Warning, removing uncomputation introduced cycles with computation ancilla nodes')
        #     logger.warning(f'Warning, removing uncomputation introduced cycles with computation ancilla nodes')
        #     print(comp_cycle_counter)
        #     logger.warning(comp_cycle_counter)

        # Find the qubit with the most number of cycles (this will include only ancilla)
        qubit, num_cycles = uncomp_cycle_counter.most_common(1)[0]
        print(qubit, num_cycles)
        # logger.info(f'The qubit {qubit} has the most number of uncomp nodes in cycles {num_cycles}')

        # Remove uncomputation for that qubit. 
        # logger.info(f'Removing all uncomputation nodes for {qubit}')
        # uncomp_circuit_graph = remove_uncomputation_full(uncomp_circuit_graph, [qubit])
        remove_uncomputation_full(uncomp_circuit_graph, [qubit])
        # logger.info(f'Time remove all uncomp nodes for {qubit} in Greedy Uncomp Circuit Graph took {time.time_ns()-start_time} ns')

        if qubit in uncomp_ancillas_list:
            uncomp_ancillas_list.remove(qubit)
        else:
            raise ValueError(f'Trying to remove qubit {qubit} not present in uncomp ancillas list {uncomp_ancillas_list}')
        
        # start_time = time.time_ns()

        cycle_check = rustworkx.digraph_find_cycle(uncomp_circuit_graph)

    if return_uncomputed_ancillas:     
        return uncomp_circuit_graph, uncomp_ancillas_list 
    else: 
        return uncomp_circuit_graph


# Greedily remove uncomputation - ALL UNCOMP NODES FOR VALID ANCILLA    
def greedy_uncomputation_full_per_node(circuit_graph: rustworkx.PyDiGraph, ancillas):
    
    start_time = time.time_ns()
    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, ancillas, allow_cycle=True)
    logger.info(f'Time to build Greedy Uncomp Circuit Graph with cycles took {time.time_ns()-start_time} ns')
    start_time = time.time_ns()

    cycle_check = rustworkx.digraph_find_cycle(uncomp_circuit_graph)
    logger.info(f'Time to check for cycle in Greedy Uncomp Circuit Graph took {time.time_ns()-start_time} ns')
    start_time = time.time_ns()
    
    while len(cycle_check) > 0:
        uncomp_cycle_counter = collections.Counter({i:0 for i in ancillas})

        for idx in uncomp_circuit_graph.node_indices():
            node = uncomp_circuit_graph.get_node_data(idx)

            if node.label in ancillas and node.node_type == UNCOMP:
                logger.info(f'Getting all simple paths for node {node}')
                all_simple_cycles_for_node = rustworkx.all_simple_paths(uncomp_circuit_graph, idx, idx)
                uncomp_cycle_counter[node.label] += len(all_simple_cycles_for_node)

        qubit, num_cycles = uncomp_cycle_counter.most_common(1)[0]
        print(qubit, num_cycles)
        logger.info(f'The qubit {qubit} has the most number of uncomp nodes in cycles {num_cycles}')

        # Remove uncomputation for that qubit. 
        logger.info(f'Removing all uncomputation nodes for {qubit}')
        uncomp_circuit_graph = remove_uncomputation_full(uncomp_circuit_graph, [qubit])

        cycle_check = rustworkx.digraph_find_cycle(uncomp_circuit_graph)

    return uncomp_circuit_graph


# Remove uncomputation of 'singular ancilla' until first node that controls ancilla is reached
def remove_uncomputation_partial(uncomp_circuit_graph:rustworkx.PyDiGraph, ancilla: str, nodes_in_cycle:List[int]):
    # uncomp_circuit_graph = copy.deepcopy(uncomp_circuit_graph)
    graph_nodes_reverse = uncomp_circuit_graph.nodes()
    graph_nodes_reverse.reverse()
    # print(graph_nodes_reverse)
    # Initialize node for this will have same index as ancilla

    # Get all outward/leaving edges of the FIRST/INIT node of the ancilla
    # This is because when we build the circuit graph, the index of INIT node is the same as the index of qubit. 
    # ancilla_idx = list(filter(lambda x: ,init_nodes))
    target_path = [x.get_index() for x in uncomp_circuit_graph.nodes() if x.label == ancilla]


    # Nodes in cycle is the list of all nodes that are a part of a cycle
    uncomp_nodes_part_of_cycle = set(nodes_in_cycle)

    # Build the list of target nodes, from INIT to last given UNCOMP

    # Get the path in descending order of node indices
    target_path.sort(reverse=True)

    # print(f'nodes_in_cycle: {nodes_in_cycle}')
    # print(f'target_path: {target_path}')
    # print(f'cycles_per_nodes: {cycles_per_nodes}')
    # print(f'uncomp_nodes_part_of_cycle: {uncomp_nodes_part_of_cycle}')
    # print(f'qubit_node_cycles: {qubit_node_cycles}')
    
    # exit(0) 

    # For each successive/predecessor node in the 'target path', check if the node in a cycle. 
    # If so, check if the node controls any ancilla. If it does, then break or else remove it. 
    for idx in target_path:
        if idx in uncomp_nodes_part_of_cycle:
            # Get all outward/leaving edges
            idx_adj_nodes = uncomp_circuit_graph.adj_direction(idx, False)
            # Get all nodes for which this node is a control and the controlled node is an uncomp node. 
            controlled_nodes = list(filter(lambda x: idx_adj_nodes.get(x) is CONTROL and uncomp_circuit_graph.get_node_data(x).node_type is UNCOMP, 
                                   idx_adj_nodes.keys()))
            # idx_cycles = qubit_node_cycles[idx]
            # print(f'{idx} : {idx_cycles}')

            # NOT SURE ABOUT THIS CHECK
            # DON'T HAVE A GOOD/CONFIDENT ARGUMENT WHY THIS WORKS
            # DON'T HAVE AN EXAMPLE WHERE IT FAILS. 
            if len(controlled_nodes) == 0:
                remove_uncomputation_step(uncomp_circuit_graph, idx)
            elif uncomp_circuit_graph.get_node_data(idx).get_mark():
                remove_uncomputation_step(uncomp_circuit_graph, idx)
            else:
                # # Note - got an example, which is why added this 
                # # break
                # for c in controlled_nodes:
                #     if rustworkx.digraph_find_cycle(circuit_graph, c):
                #         print(f'Node {idx} for qubit {circuit_graph.get_node_data(idx).label} controls node {c} of qubit {circuit_graph.get_node_data(c).label}')
                #         print(f'Node {c} is in a loop, so node {idx} will be removed')
                #         remove_uncomputation_step(circuit_graph, idx)
                #         break
                uncomp_circuit_graph.get_node_data(idx).mark_node()
                break
        
    return uncomp_circuit_graph

# Greedy - Partial Uncomp 
# Same as Greedy - Full, but has an addition dictionary that stores 
# the nodes of a qubit that are in the cycle
def greedy_uncomputation_partial(circuit_graph: rustworkx.PyDiGraph, ancillas:List[str], max_cycles:int=10**5, return_uncomputed_ancillas=False):

    # ancillas = list(range(num_qubit, num_qubit+num_ancilla))
    uncomp_circuit_graph, has_cycle = add_uncomputation(circuit_graph, ancillas, allow_cycle=True)
    
    uncomp_ancillas_list = copy.deepcopy(ancillas)

    cycle_check = rustworkx.digraph_find_cycle(uncomp_circuit_graph)

    while len(cycle_check) > 0:
        uncomp_cycle_counter = collections.Counter({i:0 for i in ancillas})
        uncomp_cycle_nodes = collections.UserDict({i:collections.UserList([]) for i in ancillas})

        simple_cycles = rustworkx.simple_cycles(uncomp_circuit_graph)
        
        # Max iterations to run the loop for, as number of cycles can 
        # easily cross 1B (and take >1day to successively parse through)        
        # max_cycles = 10**5
        cycle_counter = 0
        for cycle in tqdm(simple_cycles, desc='Iterating over all cycles', total=max_cycles):
            # print(cycle)
            for idx in cycle:
                node = uncomp_circuit_graph.get_node_data(idx)
                # node_cycle_dict[idx].append([i for i in cycle])
                if node.qubit_type is ANCILLA: 
                    if node.node_type is UNCOMP:
                        uncomp_cycle_counter[node.label] +=1
                        uncomp_cycle_nodes[node.label].append(idx)
            
            if cycle_counter > max_cycles:
                break
            
            cycle_counter += 1
            
        qubit, num_cycles = uncomp_cycle_counter.most_common(1)[0]
        print(qubit, num_cycles)

        uncomp_circuit_graph = remove_uncomputation_partial(uncomp_circuit_graph, qubit, uncomp_cycle_nodes[qubit])

        if qubit in uncomp_ancillas_list:
            uncomp_ancillas_list.remove(qubit)

        cycle_check = rustworkx.digraph_find_cycle(uncomp_circuit_graph)

    if return_uncomputed_ancillas:     
        return uncomp_circuit_graph, uncomp_ancillas_list 
    else: 
        return uncomp_circuit_graph




