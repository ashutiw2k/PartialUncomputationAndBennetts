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

