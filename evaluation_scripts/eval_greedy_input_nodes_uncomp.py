import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))  # Makes helperfunctions discoverable

import numpy as np
from rustworkx import digraph_find_cycle

from helperfunctions.randomcircuit import random_quantum_circuit_varied_percentages, get_qubits_of_circuit
from helperfunctions.reversecircuitgraph import uncompute_input_nodes_greedy, uncomp_all_operations
from helperfunctions.uncompfunctions import add_uncomputation
from helperfunctions.evaluation import plot_variable_results_better
from helperfunctions.circuitgraphfunctions import get_computation_graph, get_uncomp_circuit
from helperfunctions.constants import StringConstants

INPUT = StringConstants.INPUT.value
ANCILLA = StringConstants.ANCILLA.value
OUTPUT = StringConstants.OUTPUT.value

def evaluation_function(num_exp = 10, circ_decompose=3,
               num_q = 12, num_a = 10, num_g=50,
               percent_cc_gates = 0.8, percent_aa_gates = 0.1,
               percent_ca_gates = 0.05, percent_ac_gates = 0.05):
    
    diff_bennetts_uncomp_gates = []
    diff_greedy_uncomp_gates = []

    for i in range(num_exp):
        _circuit, q,a,g = random_quantum_circuit_varied_percentages(
            num_q=num_q, num_a=num_a, num_g=num_g, add_outputs=True,
            percent_cc_gates=percent_cc_gates, percent_aa_gates=percent_aa_gates,
            percent_ac_gates=percent_ac_gates, percent_ca_gates=percent_ca_gates)
        
        ancillae_list = get_qubits_of_circuit(_circuit, a, ANCILLA)
        outputs_list = get_qubits_of_circuit(_circuit, q, OUTPUT) 

        _computation_circuit_graph = get_computation_graph(_circuit, ancillae_list, outputs_list)
        _ancillae_full_uncomp_circuit_graph, has_cycles = add_uncomputation(_computation_circuit_graph, 
                                                           ancillae_list, allow_cycle=True)
        
        if not digraph_find_cycle(_ancillae_full_uncomp_circuit_graph):
            print(f'Iteration {i} uncomp was acyclic.')
            i -= 1
            continue
        
        _bennetts_uncomp_circuit_graph = uncomp_all_operations(_computation_circuit_graph)
        _greedy_input_uncomp_circuit_graph = uncompute_input_nodes_greedy(_ancillae_full_uncomp_circuit_graph)

        _bennetts_uncomp_circuit = get_uncomp_circuit(_bennetts_uncomp_circuit_graph)
        _greedy_input_uncomp_circuit = get_uncomp_circuit(_greedy_input_uncomp_circuit_graph)

        if circ_decompose:
            _circuit_gate_num = sum(_circuit.decompose(reps=circ_decompose).count_ops().values())
            _bennetts_uncomp_num = sum(_bennetts_uncomp_circuit.decompose(reps=circ_decompose).count_ops().values())
            _greedy_input_uncomp_num = sum(_greedy_input_uncomp_circuit.decompose(reps=circ_decompose).count_ops().values())

        else:
            _circuit_gate_num = sum(_circuit.count_ops().values())
            _bennetts_uncomp_num = sum(_bennetts_uncomp_circuit.count_ops().values())
            _greedy_input_uncomp_num = sum(_greedy_input_uncomp_circuit.count_ops().values())

        _bennetts_diff = _bennetts_uncomp_num - _circuit_gate_num
        _greedy_diff = _greedy_input_uncomp_num - _circuit_gate_num

        print(f'Bennetts Uncomp introduces {_bennetts_diff} gates to the circuit')
        print(f'Greedy Input Uncomp introduces {_greedy_diff} gates to the circuit')

        diff_bennetts_uncomp_gates.append(_bennetts_diff)
        diff_greedy_uncomp_gates.append(_greedy_diff)

    
    return diff_bennetts_uncomp_gates, diff_greedy_uncomp_gates

def main():
    
    avg_bennetts = []
    avg_greedy = []
    x_axis = []
    for num_gates in range(25,100,5):
        diff_bennetts, diff_greedy = evaluation_function(num_exp=3, num_g=num_gates, circ_decompose=0)
        avg_diff_bennetts = np.average(diff_bennetts)
        avg_diff_greedy = np.average(diff_greedy)
        
        print(f'For {num_gates} gates, Bennetts added {avg_diff_bennetts} and Greedy added {np.average(avg_diff_greedy)}')

        x_axis.append(num_gates)
        avg_bennetts.append(avg_diff_bennetts)
        avg_greedy.append(avg_diff_greedy)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_greedy], 
                                 data_labels=['Bennetts', 'Greedy'],
                                 figname='Plot Comparing Bennetts and Greedy Input Uncomp',
                                 image_write_path='evaluation_plots', 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Total number of computation gates',
                                 ylabel='Average number of uncomp gates added')        

    pass

if __name__ == '__main__':
    main()

