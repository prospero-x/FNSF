import sys
import os
import stat
from gyroradius import gyroradius_for_row
from debye_length import compute_debye_length_for_row
import util
from common import DATAFILES, _MACHINE_ASSIGNMENTS_FILE, _ions_of_interest, _CONFIG_FILENAME
import scientific_constants as sc
import yaml




_HPIC_EXEC = '~/hPIC/hpic_1d3v/hpic'


alt_hpic_execs = {
    'my_machine': 'hpic',
    'pc102': '~/hPIC-mikhail/hpic_1d3v/hpic',
}


"""
Values specified in the config override these defaults.
"""
_KINFO = 10  # Number of times info is printed to stdout
_KGRID = 10  # Number of times GRIDDATA is saved
_KPART = 10  # Number of times PARTICLEDATA is saved
_KFLUID = 10 # Number of times fluid data is saved
_NGyro = 10  # Number of Gyroradii per domain


def get_domain_debye_lengths(df_row, ngyro, debye_length, rg):
    """
    :param: df_row: a single row of SOLPS output data
    :param: ngyro: the number of gyroradii we want in the domain.
    :param: debye length: the debye length at this location of the divertor (m)
    :param: rg: the gyroradius of deuterium at this location (m)
    """
    ngyro = ngyro or _NGyro
    p1 = int(ngyro * rg / debye_length)
    return p1


def get_grid_points_per_debye_length(df_row):
    p2 = 1
    return p2


def get_time_steps_per_gyroperiod(df_row):
    p3 = 20
    return p3


def get_num_ion_transit_times(df_row):
    p4 = 1
    return p4


def get_num_particles_per_cell(df_row):
    p5 = 500
    return p5


def estimate_total_particle_pushes(rg, debye_length, ngyro):
    """
    estimate the number of pa
    """
    lmbda = ngyro * rg/debye_length

    # linear regression
    m = 168874526.0287417
    b = -21784812391.707676
    return int(m * lmbda + b)


def format_hPIC_command(df_row, SimID, hpic_params, ngyro, ion_list):
    command = f'{_HPIC_EXEC} -command_line '
    command += SimID + ' '

    rg = gyroradius_for_row(df_row)
    debye_length = compute_debye_length_for_row(df_row)

    total_particle_pushes = estimate_total_particle_pushes(rg, debye_length, ngyro)

    p1 = hpic_params.get('p1') or get_domain_debye_lengths(df_row, ngyro, debye_length, rg)
    p2 = hpic_params.get('p2') or get_grid_points_per_debye_length(df_row)
    p3 = hpic_params.get('p3') or get_time_steps_per_gyroperiod(df_row)
    p4 = hpic_params.get('p4') or get_num_ion_transit_times(df_row)
    p5 = hpic_params.get('p5') or get_num_particles_per_cell(df_row)
    command += ' '.join((str(p) for p in (p1, p2, p3, p4, p5))) + ' '


    B0 = df_row['|B| (T)']
    psi = df_row['Bangle (deg)']

    Te = df_row['Te (eV)']
    Ti = df_row['Ti (eV)']
    command += ' '.join(f'{x:.5f}' for x in (B0, psi, Te, Ti)) + ' '

    BC_LEFT_VALUE = 0.0
    BC_RIGHT_VALUE = 0.0
    command += f'{BC_LEFT_VALUE:.5f} {BC_RIGHT_VALUE:.5f} '

    # RF wave Frequency [rad/s
    Omega = 0.0
    RF_VOLTAGE_RIGHT = 0.0
    RF_VOLTAGE_LEFT = 0.0
    command += f'{Omega:.2f} {RF_VOLTAGE_RIGHT:.2f} {RF_VOLTAGE_LEFT:.2f} '

    # Global print and save options (defined at the top)
    kinfo = hpic_params.get('kinfo') or _KINFO
    kgrid = hpic_params.get('kgrid') or _KGRID
    kpart = hpic_params.get('kpart') or _KPART
    kfluid = hpic_params.get('kfluid') or _KFLUID
    command += f'{kinfo} {kgrid} {kpart} {kfluid} '

    # Add each species to the command line
    for ion in ion_list:
        ion_info = _ions_of_interest[ion]
        Ai = ion_info['Ai']
        Zi = ion_info['Zi']
        ni = df_row[ion]

        command += f'{Ai} {Zi} {ni:.5e} '

    """
    Pummi args
    """

    # Total number of submeshes in the domain
    N = 3
    command += f'{N} '
    # active mesh type segment in the i-th mesh
    typeflag_i = 'leftBL,uniform,rightBL'

    # number of Debye Lengths in the i-th mesh. Using a dummy value since
    # we're using "uniform"
    p1_i = f'{int(rg/debye_length)},{int(rg*ngyro/debye_length)},{int(rg/debye_length)}'

    # number of elements in the i-th submesh. Using dummy value since we're
    # using "uniform"
    Nel_i = f'40,400,40'

    # For the leftBL/rightBL, Number of minimum size cells in a Debye Length
    # for the i-th submesh. Using dummy value since we're using "uniform"
    p2_min_i = '1.0,1.0,1.0'
    command += '"' + '" "'.join((typeflag_i, p1_i, Nel_i, p2_min_i)) + '"'

    return command


def get_simulation_id(data_set_label, df_row):
    """
    One hPIC simulation per position relative to the Strike Point
    """
    separation = df_row['L-Lsep (m)']
    sign = 'plus_' if separation > 0 else 'minus_'
    simulation_id = f'{data_set_label}_sop_{sign}{abs(separation):.3f}'+ 'm_from_sp'
    return simulation_id


def mkdir(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def main():
    # Load config
    config = util.load_yaml(_CONFIG_FILENAME)
    ngyro = config.get('ngyro')
    hpic_params = config.get('hpic_params', {})
    ions = config.get('ions')
    if ions is not None:
        ion_list = [list(x.keys())[0] for x in ions]
    else:
        ion_list = sorted(_ions_of_interest.keys())



    datafiles = DATAFILES

    hpic_commands = {}
    for label, datafile in datafiles.items():
        append_to_hpic_commands(
            datafile,
            label,
            hpic_params,
            ngyro,
            ion_list,
            hpic_commands,
        )

    if len(sys.argv) > 1:
        if sys.argv[1] != 'configure-total-pushes-script':
            print('usage: python configure_simulations.py [configure-total-pushes-script]')
            return
        build_prelim_bash_script(hpic_commands)
    else:
        build_simulation_bash_scripts(hpic_commands)


def append_to_hpic_commands(
        datafile,
        data_set_label,
        hpic_params,
        ngyro,
        ion_list,

        hpic_commands):

    df = util.load_solps_data(datafile)
    for index, row in df.iterrows():
        SimID = get_simulation_id(data_set_label, row)
        hpic_command_line_args = format_hPIC_command(
            row,
            SimID,
            hpic_params,
            ngyro,
            ion_list,
        )
        hpic_commands[SimID] = hpic_command_line_args


def build_prelim_bash_script(hpic_commands):
    """
    This functino puts all of the hpic commands into one big shell script. It
    is meant to be run on a temporarily modified hPIC executable which accepts
    parameters as it normall does, but prints the total number of particle
    pushes that will happen during the simulation to STDOUT, and then
    immediately exit.
    """
    base_dir = 'scripts'
    util.mkdir(base_dir)
    prelim_script_name = f'{base_dir}/get_total_pushes.sh'
    prelim_script = open(prelim_script_name, 'w+')
    prelim_script.write('''
#!/usr/bin/env bash

# This script is meant to be run in order to let hPIC calculate the total
# number of particle pushes (i.e., number of particles * number of time steps)
# which will be involved in a given simulation.

# The goal is to use this information to characterize the amount of work associated
# with each simulation, and optimize assignments of many hPIC simulation across many
# machines.
''')
    util.mkdir(base_dir)
    for SimID, hpic_command in hpic_commands.items():
        # Write the simulation command to the bash script
        prelim_script.write(f'echo {SimID}, $({hpic_command} | tail -n 1)\n')


    prelim_script.close()
    util.make_executable(prelim_script_name)


def build_simulation_bash_scripts(hpic_commands):
    machine_assignments = util.load_yaml(_MACHINE_ASSIGNMENTS_FILE)

    base_dir = 'remote_scripts/generated'
    util.mkdir(base_dir)

    for machine_name, assignments in machine_assignments.items():
        # create new bash scripts for commands. one hpic simulation is one line in the
        # bash script.
        parent_script_name = f'{base_dir}/run_hpic_fnsf_solps_{machine_name}.sh'
        parent_script = open(parent_script_name, 'w+')
        parent_script.write('''
#!/usr/bin/env bash

# Generated by configure_simulations.py

# Runs one hPIC simulation per row of data from SOLPS output
# i.e one simulation per position from the strike point

declare -a pids
i=0
''')

        # hPIC output will be saved in subdirs, the tree of which must be
        # made by a script too.
        mkdir_script_filename = f'{base_dir}/mkdirs_{machine_name}.sh'
        mkdir_script = open(mkdir_script_filename, 'w+')
        mkdir_script.write('#!/usr/bin/env bash\n')

        for SimID in assignments:
            hpic_command = hpic_commands[SimID]

            if machine_name in alt_hpic_execs:
                alt_hpic_exec = alt_hpic_execs[machine_name]
                hpic_command = hpic_command.replace(_HPIC_EXEC, alt_hpic_exec)

            # Before the simulation script runs, another script must parse it
            # and create all the necessary directories

            simulation_dir = f'hpic_results/{SimID}'
            mkdir_script.write(f'mkdir -p {simulation_dir}\n')
            simulation_script_name = f'{base_dir}/{SimID}_{machine_name}.sh'
            simulation_script = open(simulation_script_name, 'w+')

            # Write the simulation command to the bash script
            simulation_script.write(f'''
#!/usr/bin/env bash

# Run the simulation for {SimID}
cd {simulation_dir}
date +%Y-%m-%dT%H:%M:%S-%Z > simulation-start
{hpic_command} > hpic.log 2>&1
if [ $? -eq 0 ]; then
    date +%Y-%m-%dT%H:%M:%S-%Z > simulation-complete
fi
''')

            simulation_script.close()
            util.make_executable(simulation_script_name)

            child_script_name = simulation_script_name.replace(f'{base_dir}/', '')
            parent_script.write(f'''
./{child_script_name} &
pids[$i]=$!
i=$((i+1))''')

        parent_script.write('''
# wait for everyone to finish
for pid in ${pids[*]};do
    wait $pid
done''')
        parent_script.close()
        util.make_executable(parent_script_name)

        mkdir_script.close()
        util.make_executable(mkdir_script_filename)


if __name__ == '__main__':
    main()
