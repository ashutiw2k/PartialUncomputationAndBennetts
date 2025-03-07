import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))  # Makes helperfunctions discoverable

import numpy as np
from rustworkx import digraph_find_cycle

from helperfunctions.randomcircuit import random_quantum_circuit_varied_percentages, get_qubits_of_circuit
from helperfunctions.reversecircuitgraph import get_bennetts_reduced_uncomp_without_reordering, remove_nodes_not_in_bennetts, uncomp_all_operations_using_circuitgraph
from helperfunctions.uncompfunctions import add_uncomputation
from helperfunctions.evaluation import plot_variable_results_better
from helperfunctions.circuitgraphfunctions import get_computation_graph, get_uncomp_circuit
from helperfunctions.graphhelper import node_matcher

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

    i = 0
    while i < num_exp:
        _circuit, q,a,g = random_quantum_circuit_varied_percentages(
            num_q=num_q, num_a=num_a, num_g=num_g, add_outputs=True, add_init=False,
            percent_cc_gates=percent_cc_gates, percent_aa_gates=percent_aa_gates,
            percent_ac_gates=percent_ac_gates, percent_ca_gates=percent_ca_gates)
        
        ancillae_list = get_qubits_of_circuit(_circuit, a, ANCILLA)
        outputs_list = get_qubits_of_circuit(_circuit, q, OUTPUT) 


        i += 1

        # Uncomputation by adding all the gates/nodes to the CG        
        _computation_circuit_graph = get_computation_graph(_circuit, ancillae_list, outputs_list)
        _all_full_uncomp_circuit_graph = uncomp_all_operations_using_circuitgraph(_computation_circuit_graph)
        _all_uncomp_circuit = get_uncomp_circuit(_all_full_uncomp_circuit_graph)
        
        # Uncomputation by just bennetts, no reordering but forcing to drop gates between inputs that occour after all ancillary uncomputation
        _reduced_input_uncomp_circuit = get_bennetts_reduced_uncomp_without_reordering(_circuit, ancillae_list, g)

        if circ_decompose:
            _circuit_gate_num = sum(_circuit.decompose(reps=circ_decompose).count_ops().values())
            _bennetts_uncomp_num = sum(_all_uncomp_circuit.decompose(reps=circ_decompose).count_ops().values())
            _greedy_input_uncomp_num = sum(_reduced_input_uncomp_circuit.decompose(reps=circ_decompose).count_ops().values())

        else:
            _circuit_gate_num = sum(_circuit.count_ops().values())
            _bennetts_uncomp_num = sum(_all_uncomp_circuit.count_ops().values())
            _greedy_input_uncomp_num = sum(_reduced_input_uncomp_circuit.count_ops().values())

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
    out_file = open('eval_logs.txt', 'w')
    for num_gates in range(25,100,5):
        diff_bennetts, diff_greedy = evaluation_function(num_exp=10, num_g=num_gates, circ_decompose=0)
        avg_diff_bennetts = np.average(diff_bennetts)
        avg_diff_greedy = np.average(diff_greedy)
        
        print(f'For {num_gates} gates, Bennetts added {avg_diff_bennetts} and Reduced Bennets added {np.average(avg_diff_greedy)}', file=out_file)

        x_axis.append(num_gates)
        avg_bennetts.append(avg_diff_bennetts)
        avg_greedy.append(avg_diff_greedy)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_greedy], 
                                 data_labels=['Bennetts', 'Reduced Bennetts'],
                                 figname='Plot Comparing Bennetts and Reduced Bennetts Uncomp',
                                 image_write_path='evaluation_plots', 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Total number of computation gates',
                                 ylabel='Average number of uncomp gates added', yfont=16,
                                 legends=True)        

    out_file.close()

if __name__ == '__main__':
    main()

