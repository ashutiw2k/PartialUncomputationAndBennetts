import os
from typing import Literal
import numpy
from qiskit import QuantumCircuit
from qiskit.quantum_info import Statevector, state_fidelity, partial_trace
from matplotlib import pyplot as plt
import matplotlib.colors as mcolors
from scipy.spatial.distance import euclidean, cityblock, jensenshannon
from scipy.stats import wasserstein_distance
from helperfunctions.measurecircuit import get_computation_qubit_probabilty, get_probability_from_statevector, get_statevector, print_probs, zero_ancillas_in_statevector
from helperfunctions.matplotlib_basic_units import radians

class NumAncillaUncomped:
    def __init__(self) -> None:
        self.exhaustive = []
        self.num_exhaustive = []
        self.greedy_full = []
        self.num_greedy_full = []
        self.greedy_partial = []
        self.num_greedy_partial = []
        self.regular = []
        self.num_regular = []
    
    def add_exhaustive(self, ancillas):
        self.exhaustive.append(ancillas)
        self.num_exhaustive.append(len(ancillas))

    def add_greedy_full(self, ancillas):
        self.greedy_full.append(ancillas)
        self.num_greedy_full.append(len(ancillas))

    def add_greedy_partial(self, ancillas):
        self.greedy_partial.append(ancillas)
        self.num_greedy_partial.append(len(ancillas))

    def add_regular(self, ancillas):
        self.regular.append(ancillas)
        self.num_regular.append(len(ancillas))

        
        self.exhaustive.append(ancillas)
        self.num_exhaustive.append(len(ancillas))

        self.greedy_full.append(ancillas)
        self.num_greedy_full.append(len(ancillas))

        self.greedy_partial.append(ancillas)
        self.num_greedy_partial.append(len(ancillas))



    def get_all_nums(self):
        return self.num_exhaustive, self.num_greedy_full, self.num_greedy_partial
    
    def __str__(self):
        vals = numpy.round(numpy.mean(self.get_all_nums(), axis=1))
        assert len(vals) == 3
        return f'''
            Avg Ancilla Uncomped Exhaustive: {vals[0]}
            Avg Ancilla Uncomped Greedy-Full: {vals[1]}
            Avg Ancilla Uncomped Greedy-Partial: {vals[2]}
            '''
        
class ProbDiffResults:
    def __init__(self, valid_num_circuits):
        self.exhaustive_comp_diff = numpy.zeros(valid_num_circuits)
        self.exhaustive_uncomp_diff = numpy.zeros(valid_num_circuits)
        self.exhaustive_eq4 = numpy.zeros(valid_num_circuits)
        self.exhaustive_eq5 = numpy.zeros(valid_num_circuits)
        self.exhaustive_uncomp = numpy.zeros(valid_num_circuits)
        

        self.greedy_full_comp_diff = numpy.zeros(valid_num_circuits)
        self.greedy_full_uncomp_diff = numpy.zeros(valid_num_circuits)
        self.greedy_full_eq4 = numpy.zeros(valid_num_circuits)
        self.greedy_full_eq5 = numpy.zeros(valid_num_circuits)
        self.greedy_full_uncomp = numpy.zeros(valid_num_circuits)
        
        self.greedy_partial_comp_diff = numpy.zeros(valid_num_circuits)
        self.greedy_partial_uncomp_diff = numpy.zeros(valid_num_circuits)        
        self.greedy_partial_eq4 = numpy.zeros(valid_num_circuits)
        self.greedy_partial_eq5 = numpy.zeros(valid_num_circuits)
        self.greedy_partial_uncomp = numpy.zeros(valid_num_circuits)

        self.regular_comp_diff = numpy.zeros(valid_num_circuits)
        self.regular_uncomp_diff = numpy.zeros(valid_num_circuits)
        self.regular_eq4 = numpy.zeros(valid_num_circuits)
        self.regular_eq5 = numpy.zeros(valid_num_circuits)
        self.regular_uncomp = numpy.zeros(valid_num_circuits)

    def add_to_exhaustive(self, comp_diff, uncomp_diff, eq4, eq5, uncomp, idx):
        # numpy.append(self.exhaustive_uncomp_diff, comp)
        # numpy.append(self.exhaustive_uncomp_diff, uncomp)
        self.exhaustive_comp_diff[idx] = comp_diff
        self.exhaustive_uncomp_diff[idx] = uncomp_diff
        # self.exhaustive_eq4[idx] = eq4
        # self.exhaustive_eq5[idx] = eq5
        # self.exhaustive_uncomp[idx] = uncomp


    def add_to_greedy_partial(self, comp_diff, uncomp_diff, eq4, eq5, uncomp, idx):
        # numpy.append(self.exhaustive_uncomp_diff, comp)
        # numpy.append(self.exhaustive_uncomp_diff, uncomp)
        self.greedy_partial_comp_diff[idx] = comp_diff
        self.greedy_partial_uncomp_diff[idx] = uncomp_diff
        # self.greedy_partial_eq4[idx] = eq4
        # self.greedy_partial_eq5[idx] = eq5
        # self.greedy_partial_uncomp[idx] = uncomp
    
    def add_to_greedy_full(self, comp_diff, uncomp_diff, eq4, eq5, uncomp, idx):
        # numpy.append(self.exhaustive_uncomp_diff, comp)
        # numpy.append(self.exhaustive_uncomp_diff, uncomp)
        self.greedy_full_comp_diff[idx] = comp_diff
        self.greedy_full_uncomp_diff[idx] = uncomp_diff
        # self.greedy_full_eq4[idx] = eq4
        # self.greedy_full_eq5[idx] = eq5
        # self.greedy_full_uncomp[idx] = uncomp
    
    def add_to_regular(self, comp_diff, uncomp_diff, eq4, eq5, uncomp, idx):
        # numpy.append(self.exhaustive_uncomp_diff, comp)
        # numpy.append(self.exhaustive_uncomp_diff, uncomp)
        self.regular_comp_diff[idx] = comp_diff
        self.regular_uncomp_diff[idx] = uncomp_diff
        # self.regular_eq4[idx] = eq4
        # self.regular_eq5[idx] = eq5
        # self.regular_uncomp[idx] = uncomp

    def __str__(self):
        return f'''
                Exhaustive Comp Avg:\t\t{numpy.average(self.exhaustive_comp_diff)}
                Exhaustive UnComp Avg:\t\t{numpy.average(self.exhaustive_uncomp_diff)}
                Greedy Full Comp Avg:\t\t{numpy.average(self.greedy_full_comp_diff)}
                Greedy Full UnComp Avg:\t\t{numpy.average(self.greedy_full_uncomp_diff)}
                Greedy Partial Comp Avg:\t{numpy.average(self.greedy_partial_comp_diff)}
                Greedy Partial UnComp Avg:\t{numpy.average(self.greedy_partial_uncomp_diff)}
                Regular Comp Avg:\t\t{numpy.average(self.regular_comp_diff)}
                Regular UnComp Avg:\t\t{numpy.average(self.regular_uncomp_diff)}
                '''

class FidelityResults:
    def __init__(self, valid_num_circuits):
        self.exhaustive_comp_fidelity = numpy.zeros(valid_num_circuits)
        self.exhaustive_uncomp_fidelity = numpy.zeros(valid_num_circuits)
        # self.exhaustive_eq4 = numpy.zeros(valid_num_circuits)
        # self.exhaustive_eq5 = numpy.zeros(valid_num_circuits)
        # self.exhaustive_uncomp = numpy.zeros(valid_num_circuits)
        

        self.greedy_full_comp_fidelity = numpy.zeros(valid_num_circuits)
        self.greedy_full_uncomp_fidelity = numpy.zeros(valid_num_circuits)
        # self.greedy_full_eq4 = numpy.zeros(valid_num_circuits)
        # self.greedy_full_eq5 = numpy.zeros(valid_num_circuits)
        # self.greedy_full_uncomp = numpy.zeros(valid_num_circuits)
        
        self.greedy_partial_comp_fidelity = numpy.zeros(valid_num_circuits)
        self.greedy_partial_uncomp_fidelity = numpy.zeros(valid_num_circuits)        
        # self.greedy_partial_eq4 = numpy.zeros(valid_num_circuits)
        # self.greedy_partial_eq5 = numpy.zeros(valid_num_circuits)
        # self.greedy_partial_uncomp = numpy.zeros(valid_num_circuits)

        self.regular_comp_fidelity = numpy.zeros(valid_num_circuits)
        self.regular_uncomp_fidelity = numpy.zeros(valid_num_circuits)
        # self.regular_eq4 = numpy.zeros(valid_num_circuits)
        # self.regular_eq5 = numpy.zeros(valid_num_circuits)
        # self.regular_uncomp = numpy.zeros(valid_num_circuits)

    def add_to_exhaustive(self, eq4comp_eq5_fidelity, eq4uncomp_eq5_fidelity, idx):
        self.exhaustive_comp_fidelity[idx] = eq4comp_eq5_fidelity
        self.exhaustive_uncomp_fidelity[idx] = eq4uncomp_eq5_fidelity
    
    def add_to_greedy_full(self, eq4comp_eq5_fidelity, eq4uncomp_eq5_fidelity, idx):
        self.greedy_full_comp_fidelity[idx] = eq4comp_eq5_fidelity
        self.greedy_full_uncomp_fidelity[idx] = eq4uncomp_eq5_fidelity
    
    def add_to_greedy_partial(self, eq4comp_eq5_fidelity, eq4uncomp_eq5_fidelity, idx):
        self.greedy_partial_comp_fidelity[idx] = eq4comp_eq5_fidelity
        self.greedy_partial_uncomp_fidelity[idx] = eq4uncomp_eq5_fidelity
    
    def add_to_regular(self, eq4comp_eq5_fidelity, eq4uncomp_eq5_fidelity, idx):
        self.regular_comp_fidelity[idx] = eq4comp_eq5_fidelity
        self.regular_uncomp_fidelity[idx] = eq4uncomp_eq5_fidelity
    
    def __str__(self):
        return f'''
                Exhaustive Comp Avg:\t\t{numpy.average(self.exhaustive_comp_fidelity)}
                Exhaustive UnComp Avg:\t\t{numpy.average(self.exhaustive_uncomp_fidelity)}
                Greedy Full Comp Avg:\t\t{numpy.average(self.greedy_full_comp_fidelity)}
                Greedy Full UnComp Avg:\t\t{numpy.average(self.greedy_full_uncomp_fidelity)}
                Greedy Partial Comp Avg:\t{numpy.average(self.greedy_partial_comp_fidelity)}
                Greedy Partial UnComp Avg:\t{numpy.average(self.greedy_partial_uncomp_fidelity)}
                Regular Comp Avg:\t\t{numpy.average(self.regular_comp_fidelity)}
                Regular UnComp Avg:\t\t{numpy.average(self.regular_uncomp_fidelity)}
                '''
    

def get_fidelitys(comp_circuit: QuantumCircuit, uncomp_circuit:QuantumCircuit, num_q, num_a):
    eq4_comp_statevector = Statevector(get_statevector(comp_circuit))
    eq4_comp_densitymat_inq_pt = partial_trace(eq4_comp_statevector, range(num_q, num_q+num_a))

    # logger.info(f'Comp Circuit {name_str} Eq4 Probability Distribution: \n{print_probs(eq4_comp_prob_dist)}')

    eq5_comp_statevector = Statevector(zero_ancillas_in_statevector(eq4_comp_statevector, num_a))
    eq5_comp_densitymat_inq_pt = partial_trace(eq5_comp_statevector, range(num_q, num_q+num_a))
    
    # logger.info(f'Comp Circuit {name_str} Eq5 Probability Distribution: \n{print_probs(eq5_comp_prob_dist)}')

    eq4_uncomp_statevector = Statevector(get_statevector(uncomp_circuit))
    eq4_uncomp_densitymat_inq_pt = partial_trace(eq4_uncomp_statevector, range(num_q, num_q+num_a))

    fidelity_eq4comp_eq5 = state_fidelity(eq4_comp_densitymat_inq_pt, eq5_comp_densitymat_inq_pt, validate=False)
    fidelity_eq4uncomp_eq5 = state_fidelity(eq4_uncomp_densitymat_inq_pt, eq5_comp_densitymat_inq_pt, validate=False)
    
    return fidelity_eq4comp_eq5, fidelity_eq4uncomp_eq5

    
    pass
        
def get_difference_in_prob(comp_circuit: QuantumCircuit, uncomp_circuit:QuantumCircuit, num_q, num_a,
                     distance:Literal['euclidean', 'manhattan', 'wasserstein', 'jensenshannon']='manhattan',
                     normalized=True):
    eq4_comp_statevector = get_statevector(comp_circuit)
    eq4_comp_prob_dist = get_probability_from_statevector(eq4_comp_statevector)
    eq4_comp_prob_dist_comp = get_computation_qubit_probabilty(eq4_comp_statevector, range(num_q), normalized)
    # logger.info(f'Comp Circuit {name_str} Eq4 Probability Distribution: \n{print_probs(eq4_comp_prob_dist)}')

    eq5_comp_statevector = zero_ancillas_in_statevector(eq4_comp_statevector, num_a)
    eq5_comp_prob_dist = get_probability_from_statevector(eq5_comp_statevector)
    eq5_comp_prob_dist_comp = get_computation_qubit_probabilty(eq5_comp_statevector, range(num_q), normalized)
    # logger.info(f'Comp Circuit {name_str} Eq5 Probability Distribution: \n{print_probs(eq5_comp_prob_dist)}')

    eq4_uncomp_statevector = get_statevector(uncomp_circuit)
    eq4_uncomp_prob_dist = get_probability_from_statevector(eq4_uncomp_statevector)
    eq4_uncomp_prob_dist_comp = get_computation_qubit_probabilty(eq4_uncomp_statevector, range(num_q), normalized)
    # logger.info(f'{uncomp_type.capitalize()} Uncomp Circuit {name_str} Eq4 Probability Distribution: \n{print_probs(eq4_uncomp_prob_dist)}')
    
    # print(numpy.sum(eq4_comp_prob_dist))
    # print_probs(eq4_comp_prob_dist)
    # print(numpy.sum(eq4_uncomp_prob_dist))
    # print_probs(eq4_uncomp_prob_dist)
    # print(numpy.sum(eq5_comp_prob_dist))
    # print_probs(eq5_comp_prob_dist)
    # assert numpy.sum(eq4_comp_prob_dist) == 1
    # assert numpy.sum(eq5_comp_prob_dist) == 1
    # assert numpy.sum(eq4_uncomp_prob_dist) == 1
    
    distance_probs_eq5_4_comp = 0
    distance_probs_eq5_4_uncomp = 0

    if distance == 'euclidean':
        distance_probs_eq5_4_comp = euclidean(eq5_comp_prob_dist_comp, eq4_comp_prob_dist_comp)
        distance_probs_eq5_4_uncomp = euclidean(eq5_comp_prob_dist_comp, eq4_uncomp_prob_dist_comp)
    elif distance == 'manhattan':
        distance_probs_eq5_4_comp = cityblock(eq5_comp_prob_dist_comp, eq4_comp_prob_dist_comp)
        distance_probs_eq5_4_uncomp = cityblock(eq5_comp_prob_dist_comp, eq4_uncomp_prob_dist_comp)
    # This is the Earth Movers Distance. 
    elif distance == 'wasserstein':
        distance_probs_eq5_4_comp = wasserstein_distance(eq5_comp_prob_dist_comp, eq4_comp_prob_dist_comp)
        distance_probs_eq5_4_uncomp = wasserstein_distance(eq5_comp_prob_dist_comp, eq4_uncomp_prob_dist_comp)
    elif distance == 'jensenshannon':
        distance_probs_eq5_4_comp = jensenshannon(eq5_comp_prob_dist_comp, eq4_comp_prob_dist_comp)
        distance_probs_eq5_4_uncomp = jensenshannon(eq5_comp_prob_dist_comp, eq4_uncomp_prob_dist_comp)

    
    
    distance_probs_eq5_4_comp, distance_probs_eq5_4_uncomp = numpy.round((distance_probs_eq5_4_comp, distance_probs_eq5_4_uncomp), decimals=10)

    return distance_probs_eq5_4_comp, distance_probs_eq5_4_uncomp, eq4_comp_prob_dist_comp, eq5_comp_prob_dist_comp, eq4_uncomp_prob_dist_comp


def plot_ancillas_bar(results_dict, figname='NEEDFIGNAME', image_write_path='NEED_IMAGE_PATH',
                 title='Number of Ancillas Uncomputed', 
                 xlabel = 'Total Number of Ancillas', 
                 ylabel = 'Average Number of Ancillas Uncomputed'):
    x_axis = []
    # ex_comp_avg = []
    ex_uncomp_avg = []
    # gf_comp_avg = []
    gf_uncomp_avg = []
    # gp_comp_avg = []
    gp_uncomp_avg = []
    
    for i,x in results_dict.items():
        # print(i)
        # print(x)
        # print('-------------------------------')
        x_axis.append(i)
        # ex_comp_avg.append(numpy.average(x.exhaustive_comp_diff))
        ex_uncomp_avg.append(numpy.round(numpy.mean(x.num_exhaustive)))
        # gf_comp_avg.append(numpy.average(x.greedy_full_comp_diff))
        gf_uncomp_avg.append(numpy.round(numpy.mean(x.num_greedy_full)))
        # gp_comp_avg.append(numpy.average(x.greedy_partial_comp_diff))
        gp_uncomp_avg.append(numpy.round(numpy.mean(x.num_greedy_partial)))

    # plt.plot(x_axis, ex_comp_avg, marker='o', linestyle='-', label='No Uncomputation')
    # plt.plot(x_axis, ex_uncomp_avg, marker='o', linestyle='-', label='Exhaustive')
    # plt.plot(x_axis, gf_uncomp_avg, marker='o', linestyle='-', label='Greedy-Full')
    # plt.plot(x_axis, gp_uncomp_avg, marker='o', linestyle='-', label='Greedy-Partial')

    # plt.legend()
    # plt.xlabel(xlabel, fontsize=14)
    # plt.ylabel(ylabel)
    # plt.title(title)
    # # fig = plt.show()
    # # plt.figure(figsize=)
    # plt.xlim(x_axis[0]-1, x_axis[-1]+1)
    # plt.autoscale(False, axis='x')
    # # plt.xscale('linear')
    # plt.savefig(f'{image_write_path}/{figname}')

    x = numpy.arange(len(x_axis))  # the label locations
    width = 0.3  # the width of the bars

    num_elements = len(x_axis)
    base_width = 6  # Minimum width
    width_per_element = 0.5  # Additional width per element
    total_width = max(base_width, base_width + (num_elements - 10) * width_per_element)
    

    fig, ax = plt.subplots(figsize=(total_width, 6))
    # rects1 = ax.bar(x - 1.5 * width, ex_comp_avg, width, label='No Uncomputation')
    rects2 = ax.bar(x - 0.5 * width, ex_uncomp_avg, width/3, label='Exhaustive', color=mcolors.CSS4_COLORS['orange'])
    rects3 = ax.bar(x, gf_uncomp_avg, width/3, label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'])
    rects4 = ax.bar(x + 0.5 * width, gp_uncomp_avg, width/3, label='Greedy-Partial', color=mcolors.CSS4_COLORS['magenta'])

    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel)
    # ax.set_title('Multiple Bar Plots')
    ax.set_xticks(x)
    uni_I = ''
    uni_K = ''

    ax.set_xticklabels(x_axis)
    ax.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
            ncol=5, mode="expand", borderaxespad=0)
    
    all_data = ex_uncomp_avg+gf_uncomp_avg+gp_uncomp_avg  # Combine all data
    min_value = min(all_data)
    max_value = max(all_data)

    # Calculate the y-axis limits
    y_min = min(0, min_value - 0.1 * min_value)  # 10% below the smallest value or 0, whichever is smaller
    y_max = max_value + 0.1 * max_value  # 10% above the largest value

    # Set the y-axis limits
    ax.set_ylim(y_min, y_max)

    # Add some padding to the top and bottom of the plot
    plt.margins(y=0.1)

    # Show the plot
    plt.tight_layout()
    plt.savefig(f'{image_write_path}/{figname}')
    plt.close()
    


def plot_ancilla_results(results_dict, figname='NEEDFIGNAME', image_write_path='NEED_IMAGE_PATH',
                 title='Number of Ancillas Uncomputed', 
                 xlabel = 'Total Number of Ancillas', 
                 ylabel = 'Average Number of Ancillas Uncomputed'):
    x_axis = []
    # ex_comp_avg = []
    ex_uncomp_avg = []
    # gf_comp_avg = []
    gf_uncomp_avg = []
    # gp_comp_avg = []
    gp_uncomp_avg = []
    
    for i,x in results_dict.items():
        # print(i)
        # print(x)
        # print('-------------------------------')
        x_axis.append(i)
        # nums = x.get_all_nums()
        # ex_comp_avg.append(numpy.average(x.exhaustive_comp_diff))
        ex_uncomp_avg.append(numpy.round(numpy.mean(x.num_exhaustive)))
        # gf_comp_avg.append(numpy.average(x.greedy_full_comp_diff))
        gf_uncomp_avg.append(numpy.round(numpy.mean(x.num_greedy_full)))
        # gp_comp_avg.append(numpy.average(x.greedy_partial_comp_diff))
        gp_uncomp_avg.append(numpy.round(numpy.mean(x.num_greedy_partial)))

    # plt.plot(x_axis, ex_comp_avg, marker='o', linestyle='-', label='Original')
    plt.plot(x_axis, ex_uncomp_avg, marker='o', linestyle='-', label='Exhaustive', color=mcolors.CSS4_COLORS['orange'])
    plt.plot(x_axis, gf_uncomp_avg, marker='o', linestyle='-', label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'])
    plt.plot(x_axis, gp_uncomp_avg, marker='o', linestyle='-', label='Greedy-Partial', color=mcolors.CSS4_COLORS['magenta'])

    # plt.xticks(numpy.arange(len(x_axis)), x_axis)
    # plt.set_xticklabels(x_axis)

    plt.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
            ncol=5, mode="expand", borderaxespad=0)
    
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel)
    # plt.title(title)
    # fig = plt.show()
    # plt.figure(figsize=)
    plt.xlim(x_axis[0]-1, x_axis[-1]+1)
    plt.autoscale(False, axis='x')
    # plt.xscale('linear')
    plt.savefig(f'{image_write_path}{figname}')
    plt.close()

def plot_results_bar(results_dict, figname='NEEDFIGNAME', image_write_path='NEED_IMAGE_PATH',
                 title='Difference In Probability - All Methods', 
                 xlabel = 'Number of (C-Not) Gates', 
                 ylabel = 'Difference in Probability Distribution'):
    x_axis = []
    ex_comp_avg = []
    ex_uncomp_avg = []
    gf_comp_avg = []
    gf_uncomp_avg = []
    gp_comp_avg = []
    gp_uncomp_avg = []
    
    for i,x in results_dict.items():
        # print(i)
        # print(x)
        # print('-------------------------------')
        x_axis.append(i)
        ex_comp_avg.append(numpy.average(x.exhaustive_comp_diff))
        ex_uncomp_avg.append(numpy.average(x.exhaustive_uncomp_diff))
        gf_comp_avg.append(numpy.average(x.greedy_full_comp_diff))
        gf_uncomp_avg.append(numpy.average(x.greedy_full_uncomp_diff))
        gp_comp_avg.append(numpy.average(x.greedy_partial_comp_diff))
        gp_uncomp_avg.append(numpy.average(x.greedy_partial_uncomp_diff))

    # plt.plot(x_axis, ex_comp_avg, marker='o', linestyle='-', label='No Uncomputation')
    # plt.plot(x_axis, ex_uncomp_avg, marker='o', linestyle='-', label='Exhaustive')
    # plt.plot(x_axis, gf_uncomp_avg, marker='o', linestyle='-', label='Greedy-Full')
    # plt.plot(x_axis, gp_uncomp_avg, marker='o', linestyle='-', label='Greedy-Partial')

    # plt.legend()
    # plt.xlabel(xlabel, fontsize=14)
    # plt.ylabel(ylabel)
    # plt.title(title)
    # # fig = plt.show()
    # # plt.figure(figsize=)
    # plt.xlim(x_axis[0]-1, x_axis[-1]+1)
    # plt.autoscale(False, axis='x')
    # # plt.xscale('linear')
    # plt.savefig(f'{image_write_path}/{figname}')

    x = numpy.arange(len(x_axis))  # the label locations
    width = 0.2  # the width of the bars

    num_elements = len(x_axis)
    base_width = 6  # Minimum width
    width_per_element = 0.5  # Additional width per element
    total_width = max(base_width, base_width + (num_elements - 10) * width_per_element)  
    fig, ax = plt.subplots(figsize=(total_width, 6))

    rects1 = ax.bar(x - 1.5 * width, ex_comp_avg, width*0.75, label='No Uncomputation', color=mcolors.CSS4_COLORS['dodgerblue'])
    rects2 = ax.bar(x - 0.5 * width, ex_uncomp_avg, width*0.75, label='Exhaustive', color=mcolors.CSS4_COLORS['orange'])
    rects3 = ax.bar(x + 0.5 * width, gf_uncomp_avg, width*0.75, label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'])
    rects4 = ax.bar(x + 1.5 * width, gp_uncomp_avg, width*0.75, label='Greedy-Partial', color=mcolors.CSS4_COLORS['magenta'])

    ax.set_xlabel(xlabel, fontsize=14)
    ax.set_ylabel(ylabel)
    # ax.set_title('Multiple Bar Plots')
    ax.set_xticks(x)
    uni_I = ''
    uni_K = ''

    ax.set_xticklabels([f'{uni_I}{i}{uni_K}' for i in x_axis])
    ax.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
            ncol=5, mode="expand", borderaxespad=0)
    
    all_data = ex_comp_avg+ex_uncomp_avg+gf_uncomp_avg+gp_uncomp_avg  # Combine all data
    min_value = min(all_data)
    max_value = max(all_data)

    # Calculate the y-axis limits
    y_min = min(0, min_value - 0.1 * min_value)  # 10% below the smallest value or 0, whichever is smaller
    y_max = max_value + 0.1 * max_value  # 10% above the largest value

    # Set the y-axis limits
    ax.set_ylim(y_min, y_max)

    # Add some padding to the top and bottom of the plot
    plt.margins(y=0.1)

    # Show the plot
    plt.tight_layout()
    plt.savefig(f'{image_write_path}/{figname}')
    plt.close()
    

def plot_results(results_dict, figname='NEEDFIGNAME', image_write_path='NEED_IMAGE_PATH',
                 title='Difference In Probability - All Methods', 
                 xlabel = 'Number of (C-Not) Gates', 
                 ylabel = 'Difference in Probability Distribution'):
    x_axis = []
    ex_comp_avg = []
    ex_uncomp_avg = []
    gf_comp_avg = []
    gf_uncomp_avg = []
    gp_comp_avg = []
    gp_uncomp_avg = []
    
    for i,x in results_dict.items():
        # print(i)
        # print(x)
        # print('-------------------------------')
        x_axis.append(i)
        ex_comp_avg.append(numpy.mean(x.exhaustive_comp_diff))
        ex_uncomp_avg.append(numpy.mean(x.exhaustive_uncomp_diff))
        # gf_comp_avg.append(numpy.average(x.greedy_full_comp_diff))
        gf_uncomp_avg.append(numpy.mean(x.greedy_full_uncomp_diff))
        # gp_comp_avg.append(numpy.average(x.greedy_partial_comp_diff))
        gp_uncomp_avg.append(numpy.mean(x.greedy_partial_uncomp_diff))

        plt.figure(figsize=(8,6))
        plt.plot(x_axis, ex_comp_avg, marker='o', markersize=12,
                 linestyle='-', label='No Uncomputation', color=mcolors.CSS4_COLORS['red'])
        plt.plot(x_axis, ex_uncomp_avg, marker='o', markersize=12, 
                linestyle='-', label='Exhaustive', color=mcolors.CSS4_COLORS['darkorange'])
        plt.plot(x_axis, gf_uncomp_avg, marker='o', markersize=8,
                linestyle='-', label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'])
        plt.plot(x_axis, gp_uncomp_avg, marker='o', markersize=4,
                linestyle='-', label='Greedy-Partial', color=mcolors.CSS4_COLORS['mediumblue'])
        plt.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
                ncol=5, mode="expand", borderaxespad=0)
    # xdiff = x_axis[1] - x_axis[0]
    # x_axis.append(x_axis[-1]+xdiff)
    # x_axis.insert(0, x_axis[0]-xdiff)
    
    # plt.xticks(numpy.arange(len(x_axis)), x_axis)
    # plt.set_xticklabels(x_axis)

    plt.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
            ncol=5, mode="expand", borderaxespad=0)
    plt.xlabel(xlabel, fontsize=14)
    plt.ylabel(ylabel, fontsize=14)
    # plt.title(title)
    # fig = plt.show()
    # plt.figure(figsize=)
    # plt.xlim(x_axis[0]-1, x_axis[-1]+1)
    # plt.autoscale(False, axis='x')



    # plt.xscale('linear')
    plt.tight_layout()
    plt.savefig(f'{image_write_path}/{figname}')
    plt.close()
    
# def format_func(value, tick_number):
#     if value == 0:
#         return "0"
#     elif value == numpy.pi:
#         return "$\\pi$"
#     elif value % (numpy.pi/6) == 0:
#         return f"{int(value/(numpy.pi/6))}$\\pi/6$"
#     else:
#         return f"{value/numpy.pi:.2f}$\\pi$"


def plot_results_angles(results_dict, figname='NEEDFIGNAME', image_write_path='NEED_IMAGE_PATH',
                 title='Difference In Probability - All Methods', 
                 xlabel = 'Angle \u03B8 (radians)', 
                 ylabel = 'Difference in Probability Distribution'):
    x_axis = []
    ex_comp_avg = []
    ex_uncomp_avg = []
    gf_comp_avg = []
    gf_uncomp_avg = []
    gp_comp_avg = []
    gp_uncomp_avg = []
    
    for i,x in results_dict.items():
        # print(i)
        # print(x)
        # print('-------------------------------')
        x_axis.append(i*numpy.pi*radians)
        ex_comp_avg.append(numpy.average(x.exhaustive_comp_diff))
        ex_uncomp_avg.append(numpy.average(x.exhaustive_uncomp_diff))
        # gf_comp_avg.append(numpy.average(x.greedy_full_comp_diff))
        gf_uncomp_avg.append(numpy.average(x.greedy_full_uncomp_diff))
        # gp_comp_avg.append(numpy.average(x.greedy_partial_comp_diff))
        gp_uncomp_avg.append(numpy.average(x.greedy_partial_uncomp_diff))

    # plt.plot(x_axis, ex_comp_avg, marker='o', linestyle='-', label='No Uncomputation', color=mcolors.CSS4_COLORS['dodgerblue'], xunits=radians)
    # plt.plot(x_axis, ex_uncomp_avg, marker='o', linestyle='-', label='Exhaustive', color=mcolors.CSS4_COLORS['orange'], xunits=radians)
    # plt.plot(x_axis, gf_uncomp_avg, marker='o', linestyle='-', label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'], xunits=radians)
    # plt.plot(x_axis, gp_uncomp_avg, marker='o', linestyle='-', label='Greedy-Partial', color=mcolors.CSS4_COLORS['magenta'], xunits=radians)
    
    plt.plot(x_axis, ex_comp_avg, marker='o', markersize=16,
             linestyle='-', label='No Uncomputation', color=mcolors.CSS4_COLORS['red'], xunits=radians)
    plt.plot(x_axis, ex_uncomp_avg, marker='o', markersize=12, 
             linestyle='-', label='Exhaustive', color=mcolors.CSS4_COLORS['darkorange'], xunits=radians)
    plt.plot(x_axis, gf_uncomp_avg, marker='o', markersize=8,
             linestyle='-', label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'], xunits=radians)
    plt.plot(x_axis, gp_uncomp_avg, marker='o', markersize=4,
             linestyle='-', label='Greedy-Partial', color=mcolors.CSS4_COLORS['mediumblue'], xunits=radians)


    plt.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
            ncol=5, mode="expand", borderaxespad=0, fontsize=9)    
    
    plt.xlabel(xlabel, fontsize=20)
    plt.ylabel(ylabel, fontsize=16)
    plt.xticks(fontsize=16)
    plt.yticks(fontsize=16)
    # plt.title(title)
    # fig = plt.show()
    # plt.figure(figsize=)
    # plt.xlim(x_axis[0]-1, x_axis[-1]+1)
    # plt.autoscale(False, axis='x')
    # plt.xscale('linear')
    plt.tight_layout()
    plt.savefig(f'{image_write_path}/{figname}')
    plt.close()
    


def plot_beautiful_ancilla_results_better(x_axis, ex_uncomp_avg, gf_uncomp_avg, gp_uncomp_avg, og=None, 
                         figname='NEEDFIGNAME', image_write_path='NEEDIMAGEPATH',
                 title='Number of Ancillas Uncomputed', 
                 xlabel = 'Total Number of Ancillas', xfont=24,
                 ylabel = 'Average Ancillae Uncomputed', yfont=24,
                 legends=False):

    fig, ax = plt.subplots(figsize=(8,6))

    if og is not None:
        ax.plot(x_axis, og, marker='o', markersize=12,
                 linestyle='-', label='No Uncomputation', color=mcolors.CSS4_COLORS['red'])
        ax.plot(x_axis, ex_uncomp_avg, marker='o', markersize=12, 
                linestyle='-', label='Exhaustive', color=mcolors.CSS4_COLORS['darkorange'])
        ax.plot(x_axis, gf_uncomp_avg, marker='o', markersize=8,
                linestyle='-', label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'])
        ax.plot(x_axis, gp_uncomp_avg, marker='o', markersize=4,
                linestyle='-', label='Greedy-Partial', color=mcolors.CSS4_COLORS['mediumblue'])
        ax.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
                ncol=5, mode="expand", borderaxespad=0)

    else:
        ax.plot(x_axis, ex_uncomp_avg, marker='o', markersize=15, 
             linestyle='-', label='Exhaustive', color=mcolors.CSS4_COLORS['darkorange'])
        ax.plot(x_axis, gf_uncomp_avg, marker='o', markersize=10,
             linestyle='-', label='Greedy-Full', color=mcolors.CSS4_COLORS['forestgreen'])
        ax.plot(x_axis, gp_uncomp_avg, marker='o', markersize=5,
             linestyle='-', label='Greedy-Partial', color=mcolors.CSS4_COLORS['mediumblue'])

    # plt.xticks(numpy.arange(len(x_axis)), x_axis)
    # plt.set_xticklabels(x_axis)

    
#     plt.xlabel(xlabel, fontsize=xfont)
#     plt.ylabel(ylabel, fontsize=yfont)
    plt.xticks(fontsize=24)
    plt.yticks(fontsize=24)


    ax.set_xlabel(xlabel, fontsize=xfont)
    ax.set_ylabel(ylabel, fontsize=yfont)    # plt.title(title)
    # ax.set_yticklabels(list(range(0,12)))
#     ax.set_xticklabels()
    # fig = plt.show()
    # plt.figure(figsize=)
#     plt.xlim(x_axis[0]-1, x_axis[-1]+1)
#     plt.ticklabel_format('{x:.0f}')
#     fig, ax = plt.subplots()
#     ax.plot
#     plt.autoscale(False, axis='x')
    # plt.xscale('linear')
    # if legends:
    #     plt.legend(bbox_to_anchor=(0, 1.01, 1, 0.2), loc='lower left',
    #         ncol=5, mode="expand", borderaxespad=0)
    #     # fig, ax = plt.plot()
        
    plt.tight_layout()
    plt.savefig(os.path.abspath(f'{image_write_path}/{figname}'))
    plt.show()
#     plt.close()

