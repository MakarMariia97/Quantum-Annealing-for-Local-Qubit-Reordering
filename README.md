# Quantum-Annealing-for-Local-Qubit-Reordering

This repository implements optimization of quantum circuits by minimizing swap count. It supplements PhD thesis titled as "Optimizing Quantum Circuit
Layout using Quantum Annealing" written by Makarova Mariia (PhD student, University of Trento, DISI). Quantum circuit optimization is performed by local reordering of qubits by boolean function in CNF and solving corresponding SAT-problem using Quantum Annealing (on D-Wave). Also, simulation mode is available. By default, Toffoli gate is optimized. It is initialized with set of gates included and dependecies between them. 

The approach is based on [Wakaki, Hattori & Yamashita, Shigeru. (2019). Mapping a Quantum Circuit to 2D Nearest Neighbor Architecture by Changing the Gate Order. IEICE Transactions on Information and Systems. E102.D. 2127-2134. 10.1587/transinf.2018EDP7439.] 
