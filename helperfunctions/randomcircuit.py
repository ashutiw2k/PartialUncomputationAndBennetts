from qiskit import QuantumCircuit, QuantumRegister
import random
import logging
import numpy as np
from numpy import pi

from tqdm import tqdm

from .graphhelper import breakdown_qubit

logger = logging.getLogger(__name__)

def get_ancillas_of_circuit(circuit, num_a):
    return [breakdown_qubit(q)['label'] for q in circuit.qubits[-num_a:]]


# Random quantum circuits generated that only allow for 
# - Input - Ancilla gates
# - Ancilla - Input gates
# Results of Greedy and Greedy Partial are the same for this. 
def random_quantum_circuit_basic() -> tuple[QuantumCircuit,int,int,int]:
    num_q = random.randint(3,10)
    num_a = random.randint(3,10)
    num_g = random.randint(10,25)
    
    in_q = QuantumRegister(num_q, name='cq')
    an_q = QuantumRegister(num_a, name='aq')
    
    circuit = QuantumCircuit(in_q, an_q)
    
    for i in range(num_g):
        
        if random.random() < 0.75: # Input acts on Ancilla    
            control_q = in_q
            target_q = an_q

        else: # Ancilla acts on input
            control_q = an_q
            target_q = in_q

        num_controls = random.randint(1, control_q.size)
        controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        target = random.randrange(target_q.size) # Get target qubit
        print(num_controls, controls, target)
        circuit.mcx([control_q[cq] for cq in controls],target_q[target]) 

    logger.info(f'Built circuit with {num_q} input, {num_a} ancilla and {num_g} gates.')
    return circuit, num_q, num_a, num_g

def random_quantum_circuit_for_partial() -> tuple[QuantumCircuit,int,int,int]:
    num_q = random.randint(3,10)
    num_a = random.randint(3,10)
    num_g = random.randint(10,25)
    
    in_q = QuantumRegister(num_q, name='cq')
    an_q = QuantumRegister(num_a, name='aq')
    
    circuit = QuantumCircuit(in_q, an_q)

    # Add random inputs
    for i in num_q:
        # circuit.rx(pi/4)
        # circuit.ry(pi/4)
        # circuit.rz(pi/4)
        circuit.h(in_q[i])
    
    for i in range(num_g):
        
        # if random.random() < 0.75: # Input acts on Ancilla    
        #     control_q = in_q
        #     target_q = an_q

        # else: # Ancilla acts on input
        #     control_q = an_q
        #     target_q = in_q
        total_q = num_q+num_a
        num_controls = random.randint(1, total_q-1)
        available_qubits = list(range(total_q))

        target = random.choice(available_qubits) # Get target qubit
        available_qubits.remove(target)
        controls = random.sample(available_qubits, num_controls)  # Get control qubit/s
        print(num_controls, controls, target)
        circuit.mcx(controls, target) 

    logger.info(f'Built circuit with {num_q} input, {num_a} ancilla and {num_g} gates.')
    return circuit, num_q, num_a, num_g

def random_quantum_circuit_large() -> tuple[QuantumCircuit,int,int,int]:
    
    num_q = random.randint(3,10)
    num_a = random.randint(3,10)
    num_g = random.randint(50, 100)
    # num_g = random.randint(10,50)
    # num_g = 75

    cc_gates = 0
    ca_gates = 0
    ac_gates = 0
    aa_gates = 0
    
    in_q = QuantumRegister(num_q, name='cq')
    an_q = QuantumRegister(num_a, name='aq')
    
    circuit = QuantumCircuit(in_q, an_q)

    for q in in_q:
        circuit.x(q)
        circuit.h(q)
    
    for i in tqdm(range(num_g), desc=f'Building Random Quantum Circuit with {num_q}q, {num_a}a, {num_g}g'):

        control_q = in_q
        target_q = in_q

        change_target_controls = random.random()

        if change_target_controls > 0.9: # Input acts on Input only    
            control_q = an_q
            target_q = an_q
            aa_gates += 1

        elif change_target_controls > 0.8: 
            # control_q = in_q
            if random.random() > 0.7:
                target_q = an_q
                ca_gates += 1
            else:
                control_q = an_q
                ac_gates += 1

        else:
            cc_gates += 1 
            

        num_controls = random.randrange(1, control_q.size)
        target = random.randrange(target_q.size) # Get target qubit
        controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        # target = random.randrange(target_q.size) # Get target qubit
        if control_q == target_q:
            target = random.randrange(target_q.size) # Get target qubit
            valid_controls = list(range(control_q.size))
            valid_controls.remove(target)
            controls = random.sample(valid_controls, num_controls)  # Get control qubit/s
        else:
            target = random.randrange(target_q.size) # Get target qubit
            controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        
        # print(num_controls, controls, target)
        circuit.mcx([control_q[cq] for cq in controls],target_q[target]) 

    logger.info(f'Built circuit with {num_q} input, {num_a} ancilla and {num_g} gates.')
    logger.info(f'There are {cc_gates} gates acting between control qubits, {ca_gates} gates acting between control and ancilla, {ac_gates} gates acting between ancilla and control and {aa_gates} gates acting between just the ancillas.')
    
    return circuit, num_q, num_a, num_g


def random_quantum_circuit_large_with_params(num_q=5, num_a=5, num_g=25,
                                            add_random_h = False,
                                            random_cz = -1, # This will be a positive float between 0,1 to randomly replace mcx with cz. 
                                            percent_aa_gates = 0.1,
                                            percent_cc_gates = 0.8,
                                            percent_switch_ca = 0.7,
                                            percent_add_h = 0.5) -> tuple[QuantumCircuit,int,int,int]:
    
    # num_q = random.randint(3,10)
    # num_a = random.randint(3,10)
    # num_g = random.randint(50, 100)
    # num_g = random.randint(10,50)
    # num_g = 75

    hc_gates = 0
    cc_gates = 0
    ca_gates = 0
    ac_gates = 0
    aa_gates = 0

    used_ancillas = []

    in_q = QuantumRegister(num_q, name='cq')
    an_q = QuantumRegister(num_a, name='aq')
    
    circuit = QuantumCircuit(in_q, an_q)

    for q in in_q:
        circuit.x(q)
        circuit.h(q)
    
    for i in tqdm(range(num_g), desc=f'Building Random Quantum Circuit with {num_q}q, {num_a}a, {num_g}g'):

        if add_random_h:
            if random.random() > percent_add_h:
                wires = random.sample(list(in_q), random.randrange(num_q))
                for w in wires:
                    circuit.h(w)
                    
                hc_gates += len(wires) 

        control_q = in_q
        target_q = in_q
        an_is_targ = False


        change_target_controls = random.random()

        if change_target_controls > 1-percent_aa_gates: # Input acts on Input only    
            control_q = an_q
            target_q = an_q
            aa_gates += 1
            an_is_targ = True

        elif change_target_controls > percent_cc_gates: 
            # control_q = in_q
            if random.random() > percent_switch_ca:
                target_q = an_q
                ca_gates += 1
                an_is_targ = True
            else:
                control_q = an_q
                ac_gates += 1

        else:
            cc_gates += 1 
            

        if an_is_targ:
            # print('an is targ')
            # print(in_q, an_q, target_q)
            val_targ = [q for q in range(target_q.size) if q not in used_ancillas]
            # print(target_q, val_targ)
            # target_q = val_tar
            # print(in_q, an_q, target_q)
        else:
            val_targ = list(range(target_q.size))
        
        if len(val_targ) == 0:
            continue

        num_controls = 1 if control_q.size == 1 else random.randrange(1, control_q.size)
        # target = random.randrange(target_q.size) if isinstance(target_q, QuantumRegister) else random.choice(target_q) # Get target qubit
        # controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        # target = random.randrange(target_q.size) # Get target qubit
        
        target = random.choice(val_targ) # Get target qubit
        if control_q == target_q:
            valid_controls = list(range(target_q.size))
            valid_controls.remove(target)
            controls = random.sample(valid_controls, num_controls)  # Get control qubit/s
        else:
            # target = random.randrange(len(target_q)) # Get target qubit
            controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        # print(controls, target, sep='--->')
        # print(num_controls, controls, target)

        if an_is_targ:
            used_ancillas.append(target)

        if random_cz > random.random():
            c = control_q[random.sample(controls,1)[0]]
            t = target_q[target]
            circuit.cz(c, t)
        else:
            circuit.mcx([control_q[cq] for cq in controls],target_q[target]) 

    logger.info(f'Built circuit with {num_q} input, {num_a} ancilla and {num_g} gates.')
    logger.info(f'There are {hc_gates} H gates acting on the control qubits, {cc_gates} gates acting between control qubits, {ca_gates} gates acting between control and ancilla, {ac_gates} gates acting between ancilla and control and {aa_gates} gates acting between just the ancillas.')
    
    return circuit, num_q, num_a, num_g

def random_quantum_circuit_varied_percentages(num_q=10, num_a=12, num_g=50,
                                            add_random_h = False,
                                            percent_cc_gates = 0.8,
                                            percent_aa_gates = 0.1,
                                            percent_ca_gates = 0.05,
                                            percent_ac_gates = 0.05,
                                            percent_add_h = 0.5) -> tuple[QuantumCircuit,int,int,int]:
    
    # num_q = random.randint(3,10)
    # num_a = random.randint(3,10)
    # num_g = random.randint(50, 100)
    # num_g = random.randint(10,50)
    # num_g = 75
    # print(f'{percent_cc_gates}+{percent_ca_gates}+{percent_ac_gates}+{percent_aa_gates} = {percent_cc_gates+percent_ca_gates+percent_ac_gates+percent_aa_gates}')
    # assert percent_cc_gates+percent_ca_gates+percent_ac_gates+percent_aa_gates == 1.0

    hc_gates = 0
    cc_gates = 0
    ca_gates = 0
    ac_gates = 0
    aa_gates = 0
    
    in_q = QuantumRegister(num_q, name='cq')
    an_q = QuantumRegister(num_a, name='aq')
    
    circuit = QuantumCircuit(in_q, an_q)

    for q in in_q:
        circuit.x(q)
        circuit.h(q)
    
    rng = np.random.default_rng()
    gate_dist = rng.random(size=num_g)

    for change_target_controls in tqdm(gate_dist, desc=f'Building Random Quantum Circuit with {num_q}q, {num_a}a, {num_g}g'):

        if add_random_h:
            if random.random() > percent_add_h:
                wires = random.sample(list(in_q), random.randrange(num_q))
                for w in wires:
                    circuit.h(w)
                    
                hc_gates += len(wires) 
        
        # Default as control-control gates
        control_q = in_q
        target_q = in_q

        if change_target_controls < percent_cc_gates:
            control_q = in_q
            target_q = in_q
            cc_gates += 1

        elif change_target_controls < percent_cc_gates + percent_ca_gates:
            control_q = in_q
            target_q = an_q
            ca_gates += 1

        elif change_target_controls < percent_cc_gates + percent_ca_gates + percent_ac_gates:
            control_q = an_q
            target_q = in_q
            ac_gates += 1

        else:
            control_q = an_q
            target_q = an_q
            aa_gates += 1
            

        num_controls = 1 if control_q.size == 1 else random.randrange(1, control_q.size)
        target = random.randrange(target_q.size) # Get target qubit
        controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        # target = random.randrange(target_q.size) # Get target qubit
        if control_q == target_q:
            target = random.randrange(target_q.size) # Get target qubit
            valid_controls = list(range(control_q.size))
            valid_controls.remove(target)
            controls = random.sample(valid_controls, num_controls)  # Get control qubit/s
        else:
            target = random.randrange(target_q.size) # Get target qubit
            controls = random.sample(range(control_q.size), num_controls)  # Get control qubit/s
        
        # print(num_controls, controls, target)
        circuit.mcx([control_q[cq] for cq in controls],target_q[target]) 

    logger.info(f'Built circuit with {num_q} input, {num_a} ancilla and {num_g} gates.')
    logger.info(f'There are {hc_gates} H gates acting on the control qubits, {cc_gates} gates acting between control qubits, {ca_gates} gates acting between control and ancilla, {ac_gates} gates acting between ancilla and control and {aa_gates} gates acting between just the ancillas.')
    
    return circuit, num_q, num_a, num_g
