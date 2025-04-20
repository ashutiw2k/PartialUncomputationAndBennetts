import sys
from pathlib import Path

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))  # Makes helperfunctions discoverable

import numpy as np
import yaml
from rustworkx import digraph_find_cycle
from qiskit import qpy

from helperfunctions.randomcircuit import random_quantum_circuit_varied_percentages, get_qubits_of_circuit, random_quantum_circuit_type_2
from helperfunctions.reversecircuitgraph import get_bennetts_reduced_uncomp_without_reordering, uncomp_all_operations_using_bennetts_in_circuitgraph, remove_input_nodes_until_required, remove_and_reorder_circuit_gates_simple, add_and_reorder_circuit_gates
from helperfunctions.uncompfunctions import add_uncomputation
from helperfunctions.evaluation import plot_variable_results_better
from helperfunctions.circuitgraphfunctions import get_computation_graph, get_uncomp_circuit
from helperfunctions.graphhelper import node_matcher

from helperfunctions.constants import StringConstants

INPUT = StringConstants.INPUT.value
ANCILLA = StringConstants.ANCILLA.value
OUTPUT = StringConstants.OUTPUT.value

NUMBER_OF_EXP = 50

def evaluation_function(num_exp = NUMBER_OF_EXP, circ_decompose=3,
               num_q = 12, num_a = 10, num_g=50,
               percent_cc_gates = 0.8, percent_aa_gates = 0.1,
               percent_ca_gates = 0.05, percent_ac_gates = 0.05):
    
    diff_bennetts_uncomp_gates = []
    diff_reduced_uncomp_gates = []
    diff_reordered_1_uncomp_gates = []
    diff_reordered_2_uncomp_gates = []
    

    i = 0
    while i < num_exp:
        _circuit, d,a,g = random_quantum_circuit_varied_percentages(
            num_d=num_q, num_a=num_a, num_g=num_g, add_outputs=True, add_init=False,
            percent_dd_gates=percent_cc_gates, percent_aa_gates=percent_aa_gates,
            percent_ad_gates=percent_ac_gates, percent_da_gates=percent_ca_gates)
        
        ancillae_list = get_qubits_of_circuit(_circuit, a, ANCILLA)
        outputs_list = get_qubits_of_circuit(_circuit, d, OUTPUT) 

        with open('random_circuit.qpy', 'wb') as file:
            qpy.dump(_circuit, file)

        # print(_circuit.draw())


        _computation_circuit_graph = get_computation_graph(_circuit, ancillae_list, outputs_list)
        
        _bennetts_uncomp_reduced_circuit = get_bennetts_reduced_uncomp_without_reordering(_circuit, ancillae_list, g)
        _bennetts_uncomp_reduced_circuit_graph = get_computation_graph(_bennetts_uncomp_reduced_circuit, ancillae_list, outputs_list)
        
        

        _ancillae_full_uncomp_circuit_graph, has_cycles = add_uncomputation(_computation_circuit_graph, 
                                                           ancillae_list, allow_cycle=True)
        
        # if not digraph_find_cycle(_ancillae_full_uncomp_circuit_graph):
        #     print(f'Iteration {i} uncomp was acyclic.')
        #     continue
        # else:

        i += 1
        

        _all_full_uncomp_circuit_graph = uncomp_all_operations_using_bennetts_in_circuitgraph(_computation_circuit_graph)
        _all_uncomp_circuit = get_uncomp_circuit(_all_full_uncomp_circuit_graph)

        # _reduced_uncomp_circuit_graph = remove_nodes_not_in_bennetts(_all_full_uncomp_circuit_graph, _bennetts_uncomp_reduced_circuit_graph, node_matcher)
        _reduced_input_circuit_graph = remove_input_nodes_until_required(_all_full_uncomp_circuit_graph)
        _reduced_input_uncomp_circuit = get_uncomp_circuit(_reduced_input_circuit_graph)

        _reordered_reduced_input_circuit_graph_1 = remove_and_reorder_circuit_gates_simple(_reduced_input_circuit_graph)
        _reordered_reduced_input_uncomp_circuit_1 = get_uncomp_circuit(_reordered_reduced_input_circuit_graph_1)

        _reordered_reduced_input_circuit_graph_2 = add_and_reorder_circuit_gates(_reduced_input_circuit_graph, _ancillae_full_uncomp_circuit_graph)
        _reordered_reduced_input_uncomp_circuit_2 = get_uncomp_circuit(_reordered_reduced_input_circuit_graph_2)


        if circ_decompose:
            _circuit_gate_num = sum(_circuit.decompose(reps=circ_decompose).count_ops().values())
            _bennetts_uncomp_num = sum(_all_uncomp_circuit.decompose(reps=circ_decompose).count_ops().values())
            _reduced_input_uncomp_num = sum(_reduced_input_uncomp_circuit.decompose(reps=circ_decompose).count_ops().values())
            _reordered_reduced_input_uncomp_num_1 = sum(_reordered_reduced_input_uncomp_circuit_1.decompose(reps=circ_decompose).count_ops().values())
            _reordered_reduced_input_uncomp_num_2 = sum(_reordered_reduced_input_uncomp_circuit_2.decompose(reps=circ_decompose).count_ops().values())
            

        else:
            _circuit_gate_num = sum(_circuit.count_ops().values())
            _bennetts_uncomp_num = sum(_all_uncomp_circuit.count_ops().values())
            _reduced_input_uncomp_num = sum(_reduced_input_uncomp_circuit.count_ops().values())            
            _reordered_reduced_input_uncomp_num_1 = sum(_reordered_reduced_input_uncomp_circuit_1.count_ops().values())
            _reordered_reduced_input_uncomp_num_2 = sum(_reordered_reduced_input_uncomp_circuit_2.count_ops().values())

        _bennetts_diff = _bennetts_uncomp_num - _circuit_gate_num
        _reduced_diff = _reduced_input_uncomp_num - _circuit_gate_num
        _reordered_diff_1 = _reordered_reduced_input_uncomp_num_1 - _circuit_gate_num
        _reordered_diff_2 = _reordered_reduced_input_uncomp_num_2 - _circuit_gate_num

        print(f'Bennetts Uncomp introduces {_bennetts_diff} gates to the circuit')
        print(f'Reduced Input Uncomp introduces {_reduced_diff} gates to the circuit')
        print(f'Reordered Reduced Input Uncomp by removing introduces {_reordered_diff_1} gates to the circuit')
        print(f'Reordered Reduced Input Uncomp by adding introduces {_reordered_diff_2} gates to the circuit')

        diff_bennetts_uncomp_gates.append(_bennetts_diff)
        diff_reduced_uncomp_gates.append(_reduced_diff)
        diff_reordered_1_uncomp_gates.append(_reordered_diff_1)
        diff_reordered_2_uncomp_gates.append(_reordered_diff_2)

    
    return diff_bennetts_uncomp_gates, diff_reduced_uncomp_gates, diff_reordered_1_uncomp_gates, diff_reordered_2_uncomp_gates

def eval_var_gates(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    
    x_axis = []
    out_file = open('eval_logs.txt', 'w')

    num_i = config_data['num_i']
    num_a = config_data['num_a']

    num_g_max = config_data['num_g_max']
    num_g_min = config_data['num_g_min']
    num_g_step = config_data['num_g_step']

    percent_cc = config_data['percent_cc']
    percent_ca = config_data['percent_ca']
    percent_ac = config_data['percent_ac']
    percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for num_gates in range(num_g_min, num_g_max+num_g_step, num_g_step):
        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                                    num_q=num_i, num_a=num_a, num_g=num_gates, circ_decompose=0,
                                                                    percent_cc_gates=percent_cc, percent_ca_gates=percent_ca, 
                                                                    percent_ac_gates=percent_ac, percent_aa_gates=percent_aa)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
        
        print(f'For {num_gates} gates, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {(avg_diff_reduced)}, Reordered Inputs by Removing added {(avg_diff_reordered_1)}, Reordered Inputs by Adding added {(avg_diff_reordered_2)}', file=out_file)

        x_axis.append(num_gates)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                 data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i}q_{num_a}a_{num_g_min}-{num_g_max}g',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Total number of Computation Gates',
                                 ylabel='Average Uncomputation Gates added', yfont=18,
                                 legends=True)        

    out_file.close()
    
def eval_var_ancilla(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    x_axis = []
    out_file = open('eval_logs.txt', 'w')

    num_i = config_data['num_i']
    num_g = config_data['num_g']

    num_a_max = config_data['num_a_max']
    num_a_min = config_data['num_a_min']
    num_a_step = config_data['num_a_step']

    percent_cc = config_data['percent_cc']
    percent_ca = config_data['percent_ca']
    percent_ac = config_data['percent_ac']
    percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for num_a in range(num_a_min, num_a_max+num_a_step, num_a_step):
        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                         num_q=num_i, num_a=num_a, num_g=num_g, circ_decompose=0,
                                                         percent_cc_gates=percent_cc, percent_ca_gates=percent_ca, 
                                                         percent_ac_gates=percent_ac, percent_aa_gates=percent_aa)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
    
        
        print(f'For {num_a} ancillae, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {(avg_diff_reduced)}, Reordered Inputs by Removing added {(avg_diff_reordered_1)}, Reordered Inputs by Adding added {(avg_diff_reordered_2)}', file=out_file)

        x_axis.append(num_a)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                 data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i}q_{num_a_min}-{num_a_max}a_{num_g}g',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Total number of ancillae',
                                 ylabel='Average number of uncomp gates added', yfont=16,
                                 legends=True)        

    out_file.close()
    
def eval_var_input(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    x_axis = []
    out_file = open('eval_logs.txt', 'w')

    num_a = config_data['num_a']
    num_g = config_data['num_g']

    num_i_max = config_data['num_i_max']
    num_i_min = config_data['num_i_min']
    num_i_step = config_data['num_i_step']

    percent_cc = config_data['percent_cc']
    percent_ca = config_data['percent_ca']
    percent_ac = config_data['percent_ac']
    percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for num_i in range(num_i_min, num_i_max+num_i_step, num_i_step):
        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                         num_q=num_i, num_a=num_a, num_g=num_g, circ_decompose=0,
                                                         percent_cc_gates=percent_cc, percent_ca_gates=percent_ca, 
                                                         percent_ac_gates=percent_ac, percent_aa_gates=percent_aa)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
        
        print(f'For {num_i} input, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {avg_diff_reduced}, Reordered Inputs by Removing added {avg_diff_reordered_1}, Reordered Inputs by Adding added {avg_diff_reordered_2}', file=out_file)

        x_axis.append(num_i)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                 data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i_min}-{num_i_max}q_{num_a}a_{num_g}g',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Total number of input qubits',
                                 ylabel='Average number of uncomp gates added', yfont=16,
                                 legends=True)        

    out_file.close()
    
    
def eval_var_percent_cc(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    x_axis = []
    out_file = open('eval_logs.txt', 'w')
    
    num_i = config_data['num_i']
    num_a = config_data['num_a']
    num_g = config_data['num_g']

    # percent_cc = config_data['percent_cc']
    # percent_ca = config_data['percent_ca']
    # percent_ac = config_data['percent_ac']
    # percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for percent in range(0, 110, 10):

        other_gates_percent = (100-percent)/300

        percent_cc = percent/100

        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                         num_q=num_i, num_a=num_a, num_g=num_g, circ_decompose=0,
                                                         percent_cc_gates=percent_cc, percent_ca_gates=other_gates_percent, 
                                                         percent_ac_gates=other_gates_percent, percent_aa_gates=other_gates_percent)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
        
        print(f'For {percent_cc} input-input, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {avg_diff_reduced}, Reordered Inputs by Removing added {avg_diff_reordered_1}, Reordered Inputs by Adding added {avg_diff_reordered_2}', file=out_file)

        x_axis.append(percent)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    # print(len(x_axis), len(avg_bennetts), len(avg_reduced), len(avg_reordered))

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                 data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i}q_{num_a}a_{num_g}g_var_percent_cc',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Percentage of Total Gates acting on Data Qubits', xfont= 16,
                                 ylabel='Average Uncomputation Gates added', yfont=18,
                                 legends=True)        

    out_file.close()
    
    
def eval_var_percent_ca(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    x_axis = []
    out_file = open('eval_logs.txt', 'w')
    
    num_i = config_data['num_i']
    num_a = config_data['num_a']
    num_g = config_data['num_g']

    # percent_cc = config_data['percent_cc']
    # percent_ca = config_data['percent_ca']
    # percent_ac = config_data['percent_ac']
    # percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for percent in range(0, 110, 10):

        other_gates_percent = (100-percent)/300

        percent_ca = percent/100

        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                         num_q=num_i, num_a=num_a, num_g=num_g, circ_decompose=0,
                                                         percent_cc_gates=other_gates_percent, percent_ca_gates=percent_ca, 
                                                         percent_ac_gates=other_gates_percent, percent_aa_gates=other_gates_percent)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
        
        print(f'For {percent_ca} input-input, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {avg_diff_reduced}, Reordered Inputs by Removing added {avg_diff_reordered_1}, Reordered Inputs by Adding added {avg_diff_reordered_2}', file=out_file)

        x_axis.append(percent)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                 data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i}q_{num_a}a_{num_g}g_var_percent_ca',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Percentage of Total Gates acting on Data-Ancilla', xfont=16,
                                 ylabel='Average Uncomputation Gates added', yfont=18,
                                 legends=True)        

    out_file.close()
     
def eval_var_percent_ac(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    x_axis = []
    out_file = open('eval_logs.txt', 'w')
    
    num_i = config_data['num_i']
    num_a = config_data['num_a']
    num_g = config_data['num_g']

    # percent_cc = config_data['percent_cc']
    # percent_ca = config_data['percent_ca']
    # percent_ac = config_data['percent_ac']
    # percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for percent in range(0, 110, 10):

        other_gates_percent = (100-percent)/300

        percent_ac = percent/100

        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                         num_q=num_i, num_a=num_a, num_g=num_g, circ_decompose=0,
                                                         percent_cc_gates=other_gates_percent, percent_ca_gates=other_gates_percent, 
                                                         percent_ac_gates=percent_ac, percent_aa_gates=other_gates_percent)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
        
        print(f'For {percent_ac} ancilla-input, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {avg_diff_reduced}, Reordered Inputs by Removing added {avg_diff_reordered_1}, Reordered Inputs by Adding added {avg_diff_reordered_2}', file=out_file)

        x_axis.append(percent)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    plot_variable_results_better(x_axis=x_axis, 
                                 data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                 data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i}q_{num_a}a_{num_g}g_var_percent_ac',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Percentage of Total Gates acting on Ancilla-Data', xfont=16,
                                 ylabel='Average Uncomputation Gates added', yfont=18,
                                 legends=True)        

    out_file.close()
    
     
def eval_var_percent_aa(config_data):
        
    avg_bennetts = []
    avg_reduced = []
    avg_reordered_1 = []
    avg_reordered_2 = []
    x_axis = []
    out_file = open('eval_logs.txt', 'w')
    
    num_i = config_data['num_i']
    num_a = config_data['num_a']
    num_g = config_data['num_g']

    # percent_cc = config_data['percent_cc']
    # percent_ca = config_data['percent_ca']
    # percent_ac = config_data['percent_ac']
    # percent_aa = config_data['percent_aa']

    img_path = config_data['fig_path']
    

    for percent in range(0, 110, 10):

        other_gates_percent = (100-percent)/300

        percent_aa = percent/100

        diff_bennetts, diff_reduced, diff_reordered_1, diff_reordered_2 = evaluation_function(num_exp=NUMBER_OF_EXP, 
                                                         num_q=num_i, num_a=num_a, num_g=num_g, circ_decompose=0,
                                                         percent_cc_gates=other_gates_percent, percent_ca_gates=other_gates_percent, 
                                                         percent_ac_gates=other_gates_percent, percent_aa_gates=percent_aa)
        avg_diff_bennetts = np.ceil(np.average(diff_bennetts))
        avg_diff_reduced = np.floor(np.average(diff_reduced))
        avg_diff_reordered_1 = np.floor(np.average(diff_reordered_1))
        avg_diff_reordered_2 = np.floor(np.average(diff_reordered_2))
        
        print(f'For {percent_aa} ancilla-ancilla, Bennetts added {avg_diff_bennetts}, Reduced Inputs added {avg_diff_reduced}, Reordered Inputs by Removing added {avg_diff_reordered_1}, Reordered Inputs by Adding added {avg_diff_reordered_2}', file=out_file)

        x_axis.append(percent)
        avg_bennetts.append(avg_diff_bennetts)
        avg_reduced.append(avg_diff_reduced)
        avg_reordered_1.append(avg_diff_reordered_1)
        avg_reordered_2.append(avg_diff_reordered_2)

    plot_variable_results_better(x_axis=x_axis, 
                                data_lists=[avg_bennetts, avg_reduced, avg_reordered_1, avg_reordered_2], 
                                data_labels=['Bennetts', 'Reduced', 'Reordered-Removing', 'Reordered-Adding'],
                                 figname=f'Plot_Bennetts_Reduced_Input_{num_i}q_{num_a}a_{num_g}g_var_percent_aa',
                                 image_write_path=img_path, 
                                 title='Average Uncomputation Gates', 
                                 xlabel='Percentage of Total Gates acting on Ancillae Qubits', xfont=16,
                                 ylabel='Average Uncomputation Gates added', yfont=18,
                                 legends=True)        

    out_file.close()

def main():
    # import yaml
    config_file = 'eval_configs/config_gates_10q12a.yaml'
    if len(sys.argv) == 2:
        config_file = sys.argv[1]
    
    with open(config_file, 'r') as f:
        data = yaml.load(f, Loader=yaml.SafeLoader)
    
        # Print the values as a dictionary
    print(data)

    if data['type'] == 'gates':
        eval_var_gates(data)
    elif data['type'] == 'ancilla':
        eval_var_ancilla(data)
    elif data['type'] == 'input':
        eval_var_input(data)
    elif data['type'] == 'cc':
        eval_var_percent_cc(data)
    elif data['type'] == 'ca':
        eval_var_percent_ca(data)
    elif data['type'] == 'ac':
        eval_var_percent_ac(data)
    elif data['type'] == 'aa':
        eval_var_percent_aa(data)




if __name__ == '__main__':
    main()

