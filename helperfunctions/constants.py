from enum import Enum
from typing import Literal


class StringConstants(Enum):
    # Types of nodes
    INIT = 'initialize'
    COMP = 'computation'
    UNCOMP = 'uncomputation'

    # Type of Qubit
    INPUT = 'input'
    ANCILLA = 'ancilla'
    OUTPUT = 'output'

    # Type of edge
    TARGET = 'target'
    CONTROL = 'control'
    ANTIDEP = 'anti-dependence'


# UNCOMP_TYPES = Literal['regular', 'exhaustive', 'greedy-full', 'greedy-partial']

class UncompType(Enum):
    REGULAR = 'regular'
    EXHAUSTIVE = 'exhaustive'
    GREEDY_FULL = 'greedy-full'
    GREEDY_PARTIAL = 'greedy-partial'

class ListConstants(Enum):

    NON_QFREE = ['h']

EVAL_DIRS = ['comp_circuit', 
             'comp_circuit_graph', 
             'comp_circuit_qpy',
             'exhaustive_uncomp_circuit',
             'exhaustive_uncomp_graph',
             'exhaustive_uncomp_circuit_qpy',
             'greedy_uncomp_circuit',
             'greedy_uncomp_graph',
             'greedy_uncomp_circuit_qpy',
             'greedy_partial_uncomp_circuit',
             'greedy_partial_uncomp_graph',
             'greedy_partial_uncomp_circuit_qpy',
             'regular_uncomp_circuit',
             'regular_uncomp_graph',
             'regular_uncomp_circuit_qpy'
             ]