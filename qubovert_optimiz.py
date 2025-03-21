from pyeda.inter import *
from pyeda.boolalg.expr import *
import itertools
from qubovert.sat import OR, NOT
from qubovert import PCBO
import numpy as np
from utils import manhattan, astar_search, annealer

# function to consruct boolean function in CNF for the circuit
def check_sat(s,nvars,ngates,nrows,ncols,x, sim):
    # condition2 (each qubit is assigned to only one cell of the grid)
    cnf1 = PCBO()
    for k in range(nvars):
        for i1,j1 in list(itertools.combinations([(i,j) for i in range(nrows) for j in range(ncols)],2)):
            cnf1.add_constraint_NAND(x[i1[0],i1[1],k],x[j1[0],j1[1],k],lam=100)
        cnf1.add_constraint_OR(*[x[i,j,k] for i in range(nrows) for j in range(ncols)],lam=10)

    # condition 3 (at most one qubit is assigned to each cellof the grid)
    for c in grid:
        for i,j in list(itertools.combinations(range(nvars),2)):
            cnf1.add_constraint_NAND(x[c[0],c[1],i],x[c[0],c[1],j],lam=100)
        
    # condition1 (interacting qubts of all gates are adjacent)
    for g in range(ngates):
        for c in range(len(grid)):
            cnf1.add_constraint_OR(NOT(x[grid[c][0],grid[c][1],s[g][0]]),OR(*[x[c1[0],c1[1],s[g][1]] for c1 in (y for y in grid if manhattan(grid[c],y)==1)]),lam=100)
            # these two OR for 3-qubit gates
    ifsat = False
    N=1 # number of repetitions (needed because of probabilistic nature of Quantum Annealing)
    indN=0
    while not ifsat and indN<N:
        Q=cnf1.to_qubo().Q # convert cnf to QUBO using qubovert package
        Qlist = list(Q.keys())
        max_i = 0
        for (i,j) in Qlist: # find dimension of QUBO
            max_i = max(i,j, max_i)
        max_i+=1

        # solve QUBO problem
        ifsat, solution = annealer(Q,cnf1,sim,k)        
        
        indN+=1

    return ifsat, solution

pr = input("Which quantum circuit would you like to optimize (Toffoli, double Toffoli, Fredkin, 2-4 decoder or CNOT-based)? Press the corresponding index (starting with 1).")
if pr == "1":
    toffoli = True
    dToffoli = False
    fredkin = False
    decod = False
    cnotbased = False
elif pr == "2":
    toffoli = False
    dToffoli = True
    fredkin = False
    decod = False
    cnotbased = False
elif pr == "3":
    toffoli = False
    dToffoli = False
    fredkin = True
    decod = False
    cnotbased = False
elif pr == "4":
    toffoli = False
    dToffoli = False
    fredkin = False
    decod = True
    cnotbased = False
elif pr == "5":
    toffoli = False
    dToffoli = False
    fredkin = False
    decod = False
    cnotbased = True
else:
        print("[ERROR] string is not valid, exiting...")
        exit(2)

if toffoli:
    # Toffoli gate
    gates=[[2,0],[1,0],[2,1],[1,0],[2,1]]
    dep_graph={2:[1]} # gate dependecies meaning that the 2nd gate in 'gates' list depends on the 1st one (starting with 0 index), etc.
    nvars = 3
elif dToffoli:
    # double Toffoli gate
    gates = [[2,1],[1,0],[3,0],[1,0],[3,0],[1,3],[2,1]]
    dep_graph = {1:[0], 2:[1], 3:[2], 4:[3], 5:[0], 6:[3,5]}
    nvars = 4
elif fredkin:
    # Fredkin gate
    gates = [[2,1],[0,2],[1,2],[0,1],[1,2],[2,1],[0,1]]
    dep_graph = {1:[0], 2:[0], 3:[2], 4:[3], 5:[1,4], 6:[5]}
    nvars = 3
elif decod:
    # 2-4 decoder
    gates=[[2,1],[3,1],[3,0],[0,2],[2,1],[1,2],[2,0],[1,3]]
    dep_graph={3:[0,2], 4:[3], 5:[4], 6:[5], 7:[1,2,4]}
    nvars = 4
else:
    # CNOT-based circuit
    gates=[[0,2],[1,3],[3,4],[1,4],[0,3],[0,2]]
    dep_graph={2:[1], 4:[2]}  # gate dependecies meaning that the 2nd gate in 'gates' list depends on the 1st one (starting with 0 index), etc.
    nvars = 5

pr1 = input("Which mode would you like to run: Quantum Annealing or Simulated Annealing? Press 1 for Quantum Annealing and 0 otherwise.")
if pr1 == "1":
    sim=False
elif pr1 == "0":
    sim=True
else:
    print("[ERROR] string is not valid, exiting...")
    exit(2)

pr2 = input("Which dimension of architecture would you like to optimize the circuit for: linear or 2-dimensional? Press 1 for linear and 2 otherwise.")
if pr2 == "1":
    nrows=1
    ncols=nvars
elif pr2 == "2":
    nrows=2
    ncols=int(np.ceil(nvars/2))



ngates_all = len(gates)

# grid
grid = [(i,j) for i in range(nrows) for j in range(ncols)]

nsubcirc=0 # initial number of subcircuits
x = exprvars("x", (0,nrows),(0,ncols),(0,nvars)) # x_ijk = 1, if qubit q_k is placed on (i,j) cell in the grid
optimal_placements = [] # list of qubit placements presented as characteristic vector X
optimal_s= [] # list of subcicruits
free_gates = list(range(ngates_all)) # initially all gates do not belong to any subcircuit
included = [0] * ngates_all # indicate if some gate belongs to some subcircuit
excluded = [0] * ngates_all # indicate if some gate becomes free again
busy = [0] * ngates_all
while free_gates:
    free_gates = [i for i in range(len(gates)) if busy[i]==0]
    s = [gates[i] for i in free_gates if busy[i]==0]
    SATres = check_sat(s,nvars,len(s),nrows,ncols,x,sim)

    included = [0] * ngates_all
    excluded = [0] * ngates_all
    if SATres[0]==False:
        fail = len(free_gates)
        success = 0
        while (success-fail)>1 or (fail-success)>1: # binary search of satisfiable subcircuits (start with 'ngates_all' and then decrease by 2 (if fails) or add several gates (if has success))
            free_gates = list(range(ngates_all))
            included = [0] * ngates_all
            s=[] # current list of subcircuits
            ngates = int(np.floor((success+fail)/2))
            i=0 # current number of gates
            sat = False
            br=False
            while i<ngates and not br and sum(included)<nvars: # if subcircuit of size ngates has not been constructed yet
                while i<ngates and ngates>=1 and free_gates and not br: # and there are free gates
                    gate1 = [y for y in free_gates if excluded[y]==0] # take the 1st free gate
                    if (gate1):
                        gate = gates[gate1[0]]
                    else:
                        br=True
                        break
                    ind = gate1[0]
                    if ind not in dep_graph: # take into account gate dependencies
                        s.append(gate)
                        free_gates.pop(free_gates.index(ind))
                        i+=1
                        included[ind] = 1
                    else:
                        prec_gates_included = [included[prec_gate] and busy[prec_gate] for prec_gate in (y for y in dep_graph[ind])]
                        if 0 not in prec_gates_included:
                            s.append(gate)
                            i+=1
                            included[ind] = 1
                            free_gates.pop(free_gates.index(ind))
                        else:
                            excluded[ind]=1
                    busy[ind]=included[ind]
                res = check_sat(s,nvars,len(s),nrows,ncols,x,sim) # check the constructed subcircuit for satisfiability
                sat = res[0]
                sol = res[1]
                if not free_gates and sat==True:
                    fail=int(np.floor((success+fail)/2))
                if sat==True:
                    break
                else: # exclude the last gate
                    if len(s)>0:
                        gate=s[len(s)-1]
                        i1=gates.index(gate)
                        s.pop()
                        i-=1
                        excluded[i1]=1
                        busy[i1]=0
                    else:
                        break
                
            if sat==True: # add solution to list of placements
                success=int(np.floor((success+fail)/2))
                for sg in s:
                    busy[gates.index(sg)]=1
                if(len(optimal_placements)):
                    optimal_placements[nsubcirc-1]=sol
                    optimal_s[nsubcirc-1]=s
                else:
                    optimal_placements.append(sol)
                    optimal_s.append(s)
            else:
                fail=int(np.floor((success+fail)/2))
                    
            if not free_gates:
                break
    else:
        for sg in s:
            ind = [i for i in range(len(gates)) if np.array_equal(gates[i],sg) == True and busy[i]==0][0]
            busy[ind]=1
            free_gates.pop(free_gates.index(ind))
        optimal_placements.append(SATres[1])
        optimal_s.append(s)
        nsubcirc+=1

# convert characteristic vectors X (denoting qubit position) obtained for each optimal subcircuit into grid
placements = [[[-1 for x in range(ncols)] for x in range(nrows)] for p in range(len(optimal_placements))] # omit excess placements
for p in range(len(optimal_placements)):
    for (i,j) in grid:
        for (key,val) in optimal_placements[p].items():
            for k in range(nvars):
                if str(key)=='x['+str(i)+','+str(j)+','+str(k)+']' and val==1:
                    placements[p][i][j]=k

# calculates SWAPs needed to 'connect' the qubit placements
swap_count=0
for i in range(len(placements)-1):
    swap_count+=astar_search(placements[i],placements[i+1],grid,nrows,ncols,nvars)

print("PLACEMENTS:\n")
for p in range(len(placements)):
    print("subcircuit:",optimal_s[p])
    print(placements[p])
print("SWAP count:",swap_count)
