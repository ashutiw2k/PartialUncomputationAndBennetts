import qiskit
from qiskit import QuantumCircuit, transpile
from qiskit.quantum_info import Statevector, partial_trace

from qiskit_aer import AerSimulator
from qiskit_aer.quantum_info import AerStatevector
import numpy as np
from math import log2

def get_index_bitmask(num_a, num_states):
    p = log2(num_states)
    if not p.is_integer():
        raise ValueError 
    valid_states = 2**(p-num_a)
    return int(valid_states-1)

# def normalize_statevector(statevector: AerStatevector):
#     if np.sum(statevector) > 1:
#         return statevector/np.sum(statevector)
    
    return statevector

def get_statevector(circuit: QuantumCircuit):
    circuit_copy = circuit.copy()
    circuit_copy.save_statevector()
    
    # This gives us the amplitudes
    simulator = AerSimulator(method='statevector', device='GPU')

    circ = transpile(circuit_copy, simulator)

    # Run and get statevector
    result = simulator.run(circ).result()
    statevector = result.get_statevector(circ)
    return statevector

def get_probability_from_statevector(statevector: AerStatevector):
    norm_state_vector = np.abs(np.pow(statevector, 2))

    # if np.sum(norm_state_vector) > 1:
    return np.real(norm_state_vector/np.sum(norm_state_vector))

    # return np.real(norm_state_vector)

def get_computation_qubit_probabilty_from_statevector(data: Statevector, inputs):
    full_statevector = Statevector(data)

    # # get the density matrix for the first qubit by taking the partial trace
    # partial_density_matrix = partial_trace(full_statevector, ancillas)

    # partial_statevector = np.real(np.diagonal(partial_density_matrix))

    # if np.sum(partial_statevector) > 1:
    #     return partial_statevector / np.sum(partial_statevector)
    # elif 
    # return np.real(partial_statevector)
    return full_statevector.probabilities(qargs=inputs)

def get_computation_qubit_probabilty(data: QuantumCircuit | Statevector, inputs, normalized=True):
    full_statevector = Statevector(data)
    probs = full_statevector.probabilities(qargs=inputs)
    # normalized_probs = probs
    if normalized and sum(probs) != 1:
        probs = probs / sum(probs)

    return probs


# Using Kullback-Leibler-Divergence to measure the difference between the probability distributions of 2 numpy arrays
# https://hanj.cs.illinois.edu/cs412/bk3/KL-divergence.pdf
# def measure_difference_in_probability(a, b):
#     return sum(a[i] * np.log(a[i]/b[i]) for i in range(len(a)))

def zero_ancillas_in_statevector(statevector: AerStatevector, num_a: int):
    vec_len = len(statevector)
    zero_ancilla_statevec = np.zeros(vec_len, dtype='complex')
    # num_vals = int(vec_len/(2**num_a))
    # zero_ancilla_statevec = np.zeros(num_vals, dtype='complex')
    for i,x in enumerate(statevector):
        # Since the last 'num_a' values are 
        idx = i & get_index_bitmask(num_a, vec_len)
        zero_ancilla_statevec[idx] += x

    zero_ancilla_statevec[zero_ancilla_statevec < 10**(-10)] = 10**(-10)
    return zero_ancilla_statevec


def print_probs(probs_vector: AerStatevector, is_statevector=False):
    pad_len = int(log2(len(probs_vector)))
    if is_statevector:
        prob_states = get_probability_from_statevector(probs_vector)
    else:
        prob_states = probs_vector

    text_string = ''
    for i,x in enumerate(prob_states):
        # print(f'|{bin(i).split("b")[1].zfill(pad_len)}> : {x:.3f}', end=' , ')
        # text = f'|{bin(i).split("b")[1].zfill(pad_len)}> : {x:.3f}'
        # text_string = ', '.join([text_string, text])
        text_string = f'{text_string}|{bin(i).split("b")[1].zfill(pad_len)}> : {x:.3f}, '
        if (i+1) % 4 == 0:
            # print()
            text_string = f'{text_string}\n'

    print(text_string)
    print('----------------------------------------')

    return text_string