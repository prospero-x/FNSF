import sys
import os
import stat
from columns import _ions_of_interest
from compute_ion_gyroradii import gyroradius
from compute_debye_lengths import compute_debye_length_for_row
import util
import scientific_constants as sc
import yaml


"""Store parameters in this file used as arguments to hpic simulations"""
_CONFIG_FILENAME = 'config.yaml'

"""
Values specified in the config override these defaults.
"""
_KINFO = 10  # Number of times info is printed to stdout
_KGRID = 10  # Number of times GRIDDATA is saved
_KPART = 10  # Number of times PARTICLEDATA is saved
_KFLUID = 10 # Number of times fluid data is saved
_NGyro = 10  # Number of Gyroradii per domain


def get_domain_debye_lengths(df_row, ngyro):
    ngyro = ngyro or _NGyro

    # Step 1: Compute Debye length.
    debye_length = compute_debye_length_for_row(df_row)

    # Step 2: Get Maximum gyroradius for all species of interest.
    max_rg = 0
    B0 = df_row['|B| (T)']
    Ti = df_row['Ti (eV)']
    for ion, ion_info in _ions_of_interest.items():
        Ai = ion_info['Ai']
        qi = ion_info['qi'] * sc.qe

        mi = Ai * sc.amu2kg

        rg = gyroradius(Ti, mi, qi, B0)
        max_rg = max(max_rg, rg)

    p1 = int(ngyro * max_rg / debye_length)
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


def format_hPIC_command_line_args(df_row, output_dir, hpic_params, ngyro):
    cla = ''

    SimID = get_simulation_id(df_row)
    cla += SimID + ' '

    p1 = hpic_params.get('p1') or get_domain_debye_lengths(df_row, ngyro)
    p2 = hpic_params.get('p2') or get_grid_points_per_debye_length(df_row)
    p3 = hpic_params.get('p3') or get_time_steps_per_gyroperiod(df_row)
    p4 = hpic_params.get('p4') or get_num_ion_transit_times(df_row)
    p5 = hpic_params.get('p5') or get_num_particles_per_cell(df_row)
    cla += ' '.join((str(p) for p in (p1, p2, p3, p4, p5))) + ' '


    B0 = df_row['|B| (T)']
    psi = df_row['Bangle (deg)']

    Te = df_row['Te (eV)']
    Ti = df_row['Ti (eV)']
    cla += ' '.join(f'{x:.5f}' for x in (B0, psi, Te, Ti)) + ' '

    BC_LEFT_VALUE = 0.0
    BC_RIGHT_VALUE = 0.0
    cla += f'{BC_LEFT_VALUE:.5f} {BC_RIGHT_VALUE:.5f} '

    # RF wave Frequency [rad/s
    Omega = 0.0
    RF_VOLTAGE_RIGHT = 0.0
    RF_VOLTAGE_LEFT = 0.0
    cla += f'{Omega:.2f} {RF_VOLTAGE_RIGHT:.2f} {RF_VOLTAGE_LEFT:.2f} '

    # Global print and save options (defined at the top)
    kinfo = hpic_params.get('kinfo') or _KINFO
    kgrid = hpic_params.get('kgrid') or _KGRID
    kpart = hpic_params.get('kpart') or _KPART
    kfluid = hpic_params.get('kfluid') or _KFLUID
    cla += f'{kinfo} {kgrid} {kpart} {kfluid} '

    for ion, mass_info in _ions_of_interest.items():
        Ai = mass_info['Ai']
        Zi = mass_info['Zi']
        ni = df_row[ion]

        cla += f'{Ai} {Zi} {ni:.5e} '


    """
    Pummi args
    """

    # Total number of submeshes in the domain
    N = 1
    cla += f'{N} '
    # active mesh type segment in the i-th mesh
    typeflag_i = 'uniform'

    # number of Debye Lengths in the i-th mesh. Using a dummy value since
    # we're using "uniform"
    p1_i = '50'

    # number of elements in the i-th submesh. Using dummy value since we're
    # using "uniform"
    Nel_i = '60'

    # For the leftBL/rightBL, Number of minimum size cells in a Debye Length
    # for the i-th submesh. Using dummy value since we're using "uniform"
    p2_min_i = '0'
    cla += '"' + '" "'.join((typeflag_i, p1_i, Nel_i, p2_min_i)) + '"'

    return cla, SimID


def get_data_set_label(datafile):
    data_set_label = datafile.split('/')[-1].split('.')[0]
    return data_set_label


def get_simulation_id(df_row):
    """
    One hPIC simulation per position relative to the Strike Point
    """
    separation = df_row['L-Lsep (m)']
    sign = 'plus_' if separation > 0 else 'minus_'
    simulation_id = f'{sign}{abs(separation):.3f}'+ 'm_separation'
    return simulation_id


def mkdir(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def main():
    if len(sys.argv) < 2:
        print('usage: $python run_simulations.py "(inner|outer)"')
        return

    if sys.argv[1] == 'inner':
        datafile = 'solps_data/solpsTargInner.csv'
    elif sys.argv[1] == 'outer':
        datafile = 'solps_data/solpsTargOuter.csv'
    else:
        print('please specify exactly one of: "(inner|outer)"')
        return

    # Load the data
    df = util.load_solps_data(datafile)

    # Load config
    config = util.load_config(_CONFIG_FILENAME)
    ngyro = config.get('ngyro')
    hpic_params = config.get('hpic_params', {})

    # Make a directory to hold the output of all simulations
    results_dir = 'hpic_results'
    mkdir(results_dir)

    data_set_label = get_data_set_label(datafile)

    # create new bash scripts for commands. one hpic simulation is one line in the
    # bash script.
    simulation_script_filename = 'scripts/run-hpic-' + data_set_label + '.sh'
    simulation_script = open(simulation_script_filename, 'w+')
    simulation_script.write(
        '#!/usr/bin/env bash\n'
        + '\n'
        + '# Generated by configure_simulations.py\n'
        + '\n'
        + '# Runs one hPIC simulation per row of data from SOLPS output\n'
        + '# i.e one simulation per position from the strike point\n'
        + '\n'
        + '# Assumes compiled 1d3v hpic binary is in PATH\n\n\n',
    )


    # Make a directory to hold the simulation results
    data_set_output_dir = results_dir + '/' + data_set_label
    util.mkdir(data_set_output_dir)

    for index, row in df.iterrows():
        hpic_command_line_args, SimID = format_hPIC_command_line_args(
            row, data_set_output_dir, hpic_params, ngyro
        )

        # Each simulation has its own subdirectory. The hpic will run
        # in that directory and save output files there.
        simulation_dir = data_set_output_dir + '/' + SimID
        util.mkdir(data_set_output_dir + '/' + SimID)

        # Write the simulation command to the bash script
        simulation_script.write(
            f'# Run the simulation for {SimID}\n'
            + f'cd {simulation_dir}\n'
            + f'hpic -command_line {hpic_command_line_args}\n'
            + f' cd ../../..\n\n',
        )

    simulation_script.close()
    util.make_executable(simulation_script_filename)


if __name__ == '__main__':
    main()
