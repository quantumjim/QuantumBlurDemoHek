# -*- coding: utf-8 -*-

# This code is part of Qiskit.
#
# (C) Copyright IBM 2020s.
#
# This code is licensed under the Apache License, Version 2.0. You may
# obtain a copy of this license in the LICENSE.txt file in the root directory
# of this source tree or at http://www.apache.org/licenses/LICENSE-2.0.
#
# Any modifications or derivative works of this code must retain this
# copyright notice, and modified files need to carry a notice indicating
# that they have been altered from the originals.

import math
import random

from micromoth import QuantumCircuit, simulate

simple_python = True


def _kron(vec0, vec1):
    new_vec = []
    for amp0 in vec0:
        for amp1 in vec1:
            new_vec.append(amp0 * amp1)
    return new_vec


def _get_size(height):
    L = int(math.sqrt(len(height)))
    return L, L


def circuit2probs(qc):
    ket = simulate(qc, get='statevector')
    probs = []
    for amp in ket:
        try:
            probs.append(amp[0]**2 + amp[1]**2)
        except:
            probs.append(amp**2)
    return probs


def make_line(length):

    # number of bits required
    n = int(math.ceil(math.log(length) / math.log(2)))

    # iteratively build list
    line = ['0', '1']
    for j in range(n - 1):
        # first append a reverse-ordered version of the current list
        line = line + line[::-1]
        # then add a '0' onto the end of all bit strings in the first half
        for j in range(int(float(len(line)) / 2)):
            line[j] += '0'
        # and a '1' for the second half
        for j in range(int(float(len(line)) / 2), int(len(line))):
            line[j] += '1'

    return line


def normalize(ket):

    N = 0
    for amp in ket:
        try:
            N += amp[0] * amp[0] + amp[1] * amp[1]
        except:
            N += amp**2
    for j, amp in enumerate(ket):
        ket[j] = float(amp) / math.sqrt(N)
    return ket


def make_grid(Lx, Ly=None):

    # set Ly if not supplied
    if not Ly:
        Ly = Lx

    # make the lines
    line_x = make_line(Lx)
    line_y = make_line(Ly)

    # make the grid
    grid = {}
    for x in range(Lx):
        for y in range(Ly):
            grid[line_x[x] + line_y[y]] = (x, y)

    # determine length of the bit strings
    n = len(line_x[0] + line_y[0])

    return grid, n


def height2circuit(height, eps=1e-2):

    # get bit strings for the grid
    Lx, Ly = _get_size(height)
    grid, n = make_grid(Lx, Ly)

    # create required state vector
    state = [0] * (2**n)
    for bitstring in grid:
        (x, y) = grid[bitstring]
        h = height[x + y * Lx]
        state[int(bitstring, 2)] = math.sqrt(h)

    state = normalize(state)

    # define and initialize quantum circuit
    qc = QuantumCircuit(n)
    # microqiskit style
    qc.initialize(state)
    qc.name = '(' + str(Lx) + ',' + str(Ly) + ')'

    return qc


def probs2height(probs, size=None, log=False):

    # get grid info
    if size:
        (Lx, Ly) = size
    else:
        Lx = int(2**(len(list(probs.keys())[0]) / 2))
        Ly = Lx
    grid, n = make_grid(Lx, Ly)

    # set height to probs value, rescaled such that the maximum is 1
    max_h = max(probs)
    height = [0] * (Lx * Ly)
    for j, prob in enumerate(probs):
        bitstring = ('{0:0' + str(n) + 'b}').format(j)
        if bitstring in grid:
            x, y = grid[bitstring]
            height[x + y * Lx] = float(probs[j]) / max_h

    # take logs if required
    if log:
        hs = []
        for h in height:
            if h!=0:
                hs.append(h)
        min_h = min(hs)
        base = 1/min_h
        for pos in range(len(height)):
            if height[pos]>0:
                height[pos] = max(math.log(height[pos]/min_h)/math.log(base),0)
            else:
                height[pos] = 0.0

    return height


def circuit2height(qc, log=False):

    probs = circuit2probs(qc)
    try:
        # get size from circuit
        size = eval(qc.name)
    except:
        # if not in circuit name, infer it from qubit number
        L = int(2**(qc.num_qubits / 2))
        size = (L, L)
    return probs2height(probs, size=size, log=log)


def combine_circuits(qc0, qc1):

    warning = "Combined circuits should contain only initialization."

    # create a circuit with the combined number of qubits
    num_qubits = qc0.num_qubits + qc1.num_qubits
    combined_qc = QuantumCircuit(num_qubits)

    # extract statevectors for any initialization commands
    kets = [None, None]
    for j, qc in enumerate([qc0, qc1]):
        for gate in qc.data:
            assert gate[0] == 'init', warning
            kets[j] = gate[1]

    # combine into a statevector for all the qubits
    ket = None
    if kets[0] and kets[1]:
        ket = _kron(kets[0], kets[1])
    elif kets[0]:
        ket = _kron(kets[0], [1] + [0] * (2**qc1.num_qubits - 1))
    elif kets[1]:
        ket = _kron([1] + [0] * (2**qc0.num_qubits - 1), kets[1])

    # use this to initialize
    if ket:
        combined_qc.initialize(ket)

    # prevent circuit name from being used for size determination
    combined_qc.name = 'None'

    return combined_qc
