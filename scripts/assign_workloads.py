import sys
import numpy as np
import yaml
from common import _MACHINE_ASSIGNMENTS_FILE


"""
Script for determining what percentage of the total amount of work
a single hPIC simulation represents.
"""

"""
If Box Bi can run a single hPIC simulation at speed vi (particles/second),
then it should be assigned vi/sum_i^n(vi) fraction of the work.

But what if Bi has M cores? then it can process M*vi particles/second.
Therefore it should be assigned M*vi/sum_i^n(M*vi) fraction of the work.

The dictionary below represents the results of the above calculation.
"""
MACHINE_BANDWIDTHS = {
    'my_machine': 0.32 ,
    'pc85': 0.11,
    'pc101': 0.12,
    'pc102': 0.12,
    'pc103': 0.11,
    'pc201': 0.24,
}


def get_fractional_workload_of_each_simulation(datafile):
    """
    datafile is a CSV with 2 columns: SimID,TOTAL_HPIC_PARTICLE_PUSHES
    """
    pushes_for_sims = {}
    with open(datafile, 'r') as f:
        # total pushes over all simulations
        T = 0
        for line in f.readlines():
            SimID, total_pushes = line.strip().split(',')
            total_pushes = int(total_pushes)
            pushes_for_sims[SimID] = total_pushes
            T += total_pushes

    print(f'Total overal pushes: {int(T)}')
    fraction_of_work = {}
    for SimID in sorted(pushes_for_sims.keys()):
        pushes = pushes_for_sims[SimID]
        fraction_of_work[SimID] = pushes/T

    return fraction_of_work


def assign_workloads(simulation_work_fractions, machine_bandwidths):
    # Step 1: sort the simulations from least-to-most workload
    workloads = [(frac, ID) for ID, frac in simulation_work_fractions.items()]
    workloads.sort(key = lambda t: t[0])

    assert sum([w[0] for w in workloads]) <= sum([v for v in machine_bandwidths.values()])


    # Step 2: assign work, starting with the smallest chunks of work. spread
    # these small chunks across all machines to minimize the chance of
    # running out of room for the bigger chunks at the end.
    #
    # Another benefit here is that smaller simulations get assigned first,
    # which means they will run first, and we can check their results to verify
    # that the simulations are running correctly.

    machines = machine_bandwidths.keys()
    machine_assignments = {k: [] for k in machines}
    q = list(machines)
    for workload, SimID in workloads:
        first_attempt = None
        for _ in range(len(q) + 1):
            # pop a machine from the queue
            machine = q.pop()
            if first_attempt is None:
                first_attempt = machine
            elif id(machine) == id(first_attempt):
                # We made it all the way around the queue and failed to assign.
                # Just assign it to the machine with the most available bandwidth.
                max_band = 0
                most_avail_machine = q[0]
                for m in q:
                    if machine_bandwidths[m] > max_band:
                        max_band = machine_bandwidths[m]
                        most_avail_machine = m
                machine_assignments[most_avail_machine].append(SimID)
                machine_bandwidths[most_avail_machine] -= workload

            # Is it possible to assign this machine this workload without
            # exceeding the machine's capability?
            if machine_bandwidths[machine] - workload > 0:

                # assign this workload
                machine_assignments[machine].append(SimID)
                machine_bandwidths[machine] -= workload
                q = [machine] + q
                break
            q = [machine] + q

    assert sum([len(v) for v in machine_assignments.values()]) == len(workloads)
    return machine_assignments


def main():
    # CSV containing two columns: SIM_ID, TOTAL_HPIC_PARTICLE_PUSHES
    if len(sys.argv) < 2:
        print('usage: python assign_workloads.py <DATAFILE>')
        sys.exit(1)
    datafile = sys.argv[1]
    workload_fractions = get_fractional_workload_of_each_simulation(datafile)
    machine_assignments = assign_workloads(workload_fractions, MACHINE_BANDWIDTHS)

    # Save the results for configure_simulations.py to use
    with open(_MACHINE_ASSIGNMENTS_FILE, 'w') as f:
        yaml.dump(machine_assignments, f)


if __name__ == '__main__':
    main()
