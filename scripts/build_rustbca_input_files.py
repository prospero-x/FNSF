import numpy as np
import os
import toml
import util
import common
import sys
import scientific_constants as sc
import glob
import re


"""
This script is used to generate input files for RustBCA simulations.

After running this script, one directory for each energy is created, and in
each directory a subdirectory for each y-offset is created. Inside each
subdirectory, an input.toml file is created for RustBCA to use.
"""

# The minimum number of total particles (across ALL energy/angle pairs) to
# fulfill the definition of a "high resolution" simulation
HIGH_RESOLUTION_N = 1e6

# Microns
TARGET_HEIGHT = 1.0
TARGET_LENGTH = 1.0

SKIP_IONS = set([
    #'nD+1',
])

# This is how many processes each LCPP box can run
# before the effective run time doubles.
machine_core_counts = {
    'pc85': 12,
    'pc101': 12,
    'pc102': 12,
    'pc103': 12,
    'pc201': 24,
    'pc202': 24,
}

TOTAL_SIMULATIONS = 182


def get_simulations_per_machine():
    proportions = {}
    total_capacity = sum((v for v in machine_core_counts.values()))
    for machine_name, ncores in machine_core_counts.items():
        proportions[machine_name] = int(ncores * TOTAL_SIMULATIONS /total_capacity) + 1
    return proportions

def get_midpoint(p1,p2):
    x1, y1 = p1
    x2, y2 = p2
    midpoint = np.array([
        abs(x1 - x2)/2 + min(x1, x2),
        abs(y1 - y2)/2 + min(y1, y2),
        0.0,
    ])
    return midpoint

def rotate(X, theta):
    """
    Rotate a 2D vector by angle theta.
    """
    Xprime = np.copy(X)
    Xprime[0] = X[0] * np.cos(theta) - X[1] * np.sin(theta)
    Xprime[1] = X[0] * np.sin(theta) + X[1] * np.cos(theta)
    return Xprime


def get_target_boundary_points(theta = 0.0):
    b1 = rotate((-TARGET_LENGTH/2., 0), theta)
    b2 = rotate((-TARGET_LENGTH/2., -TARGET_HEIGHT), theta)
    b3 = rotate((TARGET_LENGTH/2., -TARGET_HEIGHT), theta)
    b4 = rotate((TARGET_LENGTH/2., 0), theta)
    return b1, b2, b3, b4


def get_simulation_boundary_points(broadening_factor = 0.05):
    b1, b2, b3, b4 = get_target_boundary_points()
    sb1 = (b1[0] - TARGET_LENGTH * broadening_factor, b1[1] + TARGET_HEIGHT * broadening_factor)
    sb2 = (b2[0] - TARGET_LENGTH * broadening_factor, b2[1] - TARGET_HEIGHT * broadening_factor)
    sb3 = (b3[0] + TARGET_LENGTH * broadening_factor, b3[1] - TARGET_HEIGHT * broadening_factor)
    sb4 = (b4[0] + TARGET_LENGTH* broadening_factor, b4[1] + TARGET_HEIGHT * broadening_factor)
    return sb1, sb2, sb3, sb4


def get_target_mesh_triangles():
    b1, b2, b3, b4 = get_target_boundary_points()
    triangle1 = [b2[0], b1[0], b4[0], b2[1], b1[1], b4[1]]
    triangle2 = [b2[0], b4[0], b3[0], b2[1], b3[1], b4[1]]
    return triangle1, triangle2



def generate_rustbca_input(
    name,
    particle_parameters,
    num_chunks,
    nthreads,
    input_filename,
    lithium_surface_binding_energy = 1.4):

    print(f'building {input_filename}...')
    options = {
        'name': name,
        'track_trajectories': False,
        'track_recoils': True,
        'track_displacements': False,
        'track_energy_losses': False,
        'track_recoil_trajectories': False,
        'write_buffer_size': 8000,
        'weak_collision_order': 0,
        'suppress_deep_recoils': False,
        'high_energy_free_flight_paths': False,
        'num_threads': nthreads,
        'num_chunks': num_chunks,
        'use_hdf5': False,
        'electronic_stopping_mode': 'LOW_ENERGY_NONLOCAL',
        'mean_free_path_model': 'LIQUID',
        'interaction_potential': [['KR_C']],
    }

    """
    Target Material (Lithium) properties (values from ./materials_info.txt)
    """
    # Density (atoms per cubic micron)
    # LIQUID lithium density
    n_target = 4.442103e+10

    # Bulk Binding Energy (eV). Using Heat of Formation from JP's paper
    Eb_target = 1.1

    # Cutoff energy for incident ions (eV)
    Ec_target = 1.5

    # Proton count
    Z_target = 3

    # Average Mass (amu)
    m_target = 6.941

    material_parameters = {
        'energy_unit': 'EV',
        'mass_unit': 'AMU',
        'Eb': [Eb_target],
        'Es': [lithium_surface_binding_energy],
        'Ec': [Ec_target],
        'Z': [Z_target],
        'm': [m_target] ,
        'interaction_index': [0],
        'surface_binding_model': 'AVERAGE',
        'bulk_binding_model': 'AVERAGE'
    }

    energy_barrier_thickness = n_target**(-1./3.)

    target_boundary_points = get_target_boundary_points()
    triangles = get_target_mesh_triangles()

    # 2D Mesh
    geometry_input = {
        'length_unit': 'MICRON',
        'energy_barrier_thickness': energy_barrier_thickness,
        'triangles': triangles,
        'densities': [[n_target]] * len(triangles),
        'material_boundary_points': target_boundary_points,
        'simulation_boundary_points': get_simulation_boundary_points(broadening_factor=1),
        'electronic_stopping_correction_factors': [ 1.0 ] * len(triangles) ,
    }


    input_file = {
        'material_parameters': material_parameters,
        'particle_parameters': particle_parameters,
        'geometry_input': geometry_input,
        'options': options,
    }

    with open(input_filename, 'w') as f:
        toml.dump(input_file, f, encoder=toml.TomlNumpyEncoder())

        # Since the 'options' section will be at the end (alphabetical order),
        # we can write these extra bits after the rest of the toml and they
        # will become part of the 'options' section.
        f.write(r'scattering_integral = [["MENDENHALL_WELLER"]]')
        f.write('\n')
        f.write(r'root_finder = [[{"NEWTON"={max_iterations = 100, tolerance=1E-3}}]]')


Deuterium = {
    'mass': 2.014,     # Average Mass (a.m.u.)
    'Z':  1,           # Proton Count
    'Ec': 0.95,        # Cutoff energy, eV
    'Es': 1.5,         # Surface Binding Energy, eV
}

Helium = {
    'mass': 4.002602,  # Average Mass (a.m.u.)
    'Z':  2,           # Proton Count
    'Ec': 1.0,         # Cutoff energy, eV
    'Es': 0.0,         # Surface Binding Energy, eV
}

Neon = {
    'mass': 20.1797, # Average Mass (a.m.u.)
    'Z': 10,         # Proton Count
    'Ec': 0.1,       # Cutoff Energy, eV
    'Es': 0.0,       # Surface Binding Energy, eV
}

"""
The names come from hPIC labels. These are pinned down in config.yaml, which
configures the hPIC simulations and avoids ambiguity in post-processing.
"""
incident_ions = {
    'nD+1': Deuterium,
    'nNe+1': Neon,
    'nNe+2': Neon,
    'nNe+3': Neon,
}

def angle_to_dir(angle):
    """
    take: scalar angle value, which represents a normal to the divertor
    return: a three-tuple, representing the x, y, and z direction
    """
    radians = angle * np.pi / 180
    particle_dir = np.array([np.cos(radians), -np.sin(radians), 0.0])
    return np.round(particle_dir, decimals = 5)


def get_particle_parameters_from_IEAD(
        IEAD,
        Te,
        particle,
        particle_starting_positions,
        particle_directions,
        example = False,
        factor = 1):
    """
    Incident ion properties
    """
    max_E = Te * 24.0

    # N_e = num different energy values
    N_e = 240

    # get energies.
    # first 90 elements: 0.05 * Te
    # next 90 elements:  0.15 * Te
    # ...
    # final 90 elements: 23.95 * Te
    incident_energies = [(Ei + 0.5)  * max_E / N_e for Ei in range(N_e) for _ in range(90)]


    particle_counts = IEAD.flatten()
    M = IEAD.size
    particle_parameters = {
        'length_unit': 'MICRON',
        'energy_unit': 'EV',
        'mass_unit': 'AMU',
        'N': list((particle_counts * factor).astype(int)),
        'm': [particle['mass']] * M ,
        'Z': [particle['Z']] * M,
        'E': incident_energies,
        'Ec': [particle['Ec']] * M,
        'Es': [particle['Es']]*M,
        'interaction_index': [0] * M,
        'pos': particle_starting_positions,
        'dir': particle_directions,
        'particle_input_filename': ''
    }
    if example:
        # Delete the values which will take up a lot file space,
        # so we can easily view the rustbca input file and examine
        # more interesting values like the interaction potential and
        # the integration method, etc.
        keys_with_large_values = ['E', 'N', 'm', 'Z', 'Ec', 'Es', 'pos', 'dir','interaction_index']
        for k in keys_with_large_values:
            del particle_parameters[k]
    return particle_parameters

def get_particle_parameters(
    particle,
    particle_starting_positions,
    particle_directions,
    incident_energies,
    N):

    particle_parameters = {
        'length_unit': 'MICRON',
        'energy_unit': 'EV',
        'mass_unit': 'AMU',
        'N': [N],
        'm': [particle['mass']],
        'Z': [particle['Z']],
        'E': incident_energies,
        'Ec': [particle['Ec']],
        'Es': [particle['Es']],
        'interaction_index': [0],
        'pos': particle_starting_positions,
        'dir': particle_directions,
        'particle_input_filename': ''
    }
    return particle_parameters


def get_Te_for_Lsep(Lsep, df):
    """
    Lsep: the separation from the SP (in meters)
    df: the SOLPS data, which contains one row per Lsep. Te is a column
    """
    # When the hPIC simulations were configured, Lsep was truncated at
    # 3 decimal points and converted to a string. So we need to go back
    # and inspect the SOLPS data to fiture out which row of data has
    # the closest Lsep value to the one we used for the Simulation ID,
    # i.e. find which was SOLPS data row was used to configure this
    # hPIC simulation in the first place.
    idx = df['L-Lsep (m)'].searchsorted(Lsep)
    if idx == len(df):
        idx -= 1

    # searchsorted returns the index at which WOULD be appropriate to
    # insert the requested value into the array, to preserve order.
    # Since the SOLPS data contains both +/- values, the row we are
    # looking for could be at i-1.
    NextLsep = df.iloc[idx]['L-Lsep (m)']
    PrevLsep =  df.iloc[idx-1]['L-Lsep (m)']

    if abs(NextLsep - Lsep) < abs(PrevLsep - Lsep):
        Te_eV = df.iloc[idx]['Te (eV)']
    else:
        Te_eV = df.iloc[idx-1]['Te (eV)']
    return Te_eV



def main():
    # SBE (eV). We don't know a good value for SBE, so we're estimating a range.
    lithium_surface_binding_energy = 1.0
    if len(sys.argv) >= 2:
        if sys.argv[1].lower() != 'low' and sys.argv[1].lower() != 'high':
            print('usage: python build_rustbca_input_files.py (high|low) [example]')
            sys.exit(1)
        elif sys.argv[1].lower() == 'high':
            lithium_surface_binding_energy = 4.0

    example = False
    if len(sys.argv) == 3:
        if sys.argv[2].lower() != 'example':
            print('usage: python build_rustbca_input_files.py (high|low) [example]')
            sys.exit(1)
        else:
            example = True

    SBE_label = f'SBE_{int(lithium_surface_binding_energy)}eV'

    output_dir = f'rustbca_simulations'
    if example:
        output_dir = f'rustbca_simulation_examples'
    util.mkdir(output_dir)

    # Pin down species names in a config file so we're never wondering what
    # ion "sp4" is.
    config = util.load_yaml(common._CONFIG_FILENAME)
    ion_names = common.invert_ion_map(config['ions'])


    if SKIP_IONS:
        print(f'\nSKIPPING the following ions: {SKIP_IONS}\n')
    datafiles = common.DATAFILES
    solps_data = {}
    for data_set_label, datafile in datafiles.items():
        solps_data[data_set_label] = util.load_solps_data(datafile)


    # Initialize directions head of time. This is based on the assumptino that
    # the IEAD has 240 rows (240 energies ranging from 0 to 24*Te) and 90
    # columns (one for each angle between 0 and 90)
    particle_directions = []
    particle_starting_positions = []

    # we want the particles to strike the target halfway up the left side,
    # coming from the left.
    top_left_corner, bottom_left_corner, _, _ = get_target_boundary_points()
    mesh_strike_point = get_midpoint(top_left_corner, bottom_left_corner)

    # Rotate just a tad to avoid gimball lock (x-direction cannot equal 1 )
    directions = [rotate(angle_to_dir(x), 0.0001) for x in range(90)]
    N_e = 240
    for _ in range(N_e):
        for theta in range(90):
            particle_directions.append(directions[theta])
            particle_starting_positions.append(mesh_strike_point - directions[theta])


    machine_workloads = iter(get_simulations_per_machine().items())
    machine_name, machine_capacity = next(machine_workloads)
    simulations_assigned = 0

    conversion_factor_files = {}
    for SimID in glob.glob('hpic_results/*'):
        if SimID == 'hpic_results/p2c.csv':
            continue
        dataset_for_sim = common.get_dataset_from_SimID(SimID)
        SimLsep = common.get_Lsep_from_SimID(SimID)
        Te = get_Te_for_Lsep(SimLsep, solps_data[dataset_for_sim])

        for IEADfile in glob.glob(SimID + '/*_IEAD_*.dat'):
            # Get this species name
            iead_label = re.search('IEAD_sp[0-9]{1,2}', IEADfile).group()
            species_label = iead_label.split('_')[1]
            ion_name = ion_names[species_label]
            if ion_name in SKIP_IONS:
                continue


            # include the output dir in the Sim name so the results get saved
            # to the subdirectory
            SimID = SimID.replace("hpic_results/", "")
            RustBCA_SimID = f'{SBE_label}/{SimID}{ion_name}/'
            util.mkdir(RustBCA_SimID)
            rustbca_input_file =  f'{output_dir}/{RustBCA_SimID}{machine_name}-input.toml'
            IEAD = np.genfromtxt(IEADfile, delimiter = ' ')

            # Multiply each count in the IEAD by a factor to each a total
            # number of simulation particles to count as a "high resolution"
            # simulation
            factor = 1
            if np.sum(IEAD) == 0:
                print(
                    f'Warning Iead file: "{IEADfile}" empty, no Rustbca '
                    + 'simulation will be run.',
                )
                continue
            elif np.sum(IEAD) < 1e6:
               factor = np.ceil(1e6/np.sum(IEAD))

            # Save the conversion factor
            if ion_name not in conversion_factor_files:
                fname = f'rustbca_conversion_factors/{ion_name}.csv'
                f =  open(fname, 'w+')
                conversion_factor_files[ion_name] = f
            conversion_factor_file = conversion_factor_files[ion_name]
            conversion_factor_file.write(f'{RustBCA_SimID},{factor}\n')

            simulations_assigned += 1
            if simulations_assigned == machine_capacity:
                simulations_assigned = 0
                try:
                    machine_name, machine_capacity = next(machine_workloads)
                except StopIteration:
                    pass

            continue
            incident_ion = incident_ions[ion_name]
            particle_parameters = get_particle_parameters_from_IEAD(
                IEAD,
                Te,
                incident_ion,
                particle_starting_positions,
                particle_directions,
                example = example,
                factor = factor,
            )

            num_chunks = 100
            nthreads = machine_core_counts[machine_name]

            generate_rustbca_input(
                RustBCA_SimID,
                particle_parameters,
                num_chunks,
                nthreads,
                rustbca_input_file,
                lithium_surface_binding_energy = lithium_surface_binding_energy,
            )

    for f in conversion_factor_files.values():
        f.close()


def format_single_calibration_file(lithium_surface_binding_energy):
    """
    I'm having a difficult time finding an accurate value for energy
    barrier thickness for liquid lithium. So instead I'm going to take JP's
    2003 paper on Liquid lithium sputtering rates, and fine tune a simulation
    until I can get similar results to his.
    """

    output_dir = 'rustbca_simulations'
    util.mkdir(output_dir)

    # include the outut directory in the simulation name so RustBCA
    # saves the data in the subdirectory.
    SimID = output_dir + f'/he_on_liquid_lithium_calibration/SBE_{int(lithium_surface_binding_energy)}eV/'
    util.mkdir(SimID)
    rustbca_input_filename = SimID + 'input.toml'

    # Number of incident He ions in simulation
    N = 10000

    # Figures specific to JP's paper
    # [eV]
    He_incident_E = 700
    He_incident_dir = angle_to_dir(80)

    # we want the particles to strike the target halfway up the left side,
    # coming from the left.
    top_left_corner, bottom_left_corner, _, _ = get_target_boundary_points()
    mesh_strike_point = get_midpoint(top_left_corner, bottom_left_corner)
    particle_directions = [rotate(He_incident_dir, 0.01)]
    particle_starting_positions = [mesh_strike_point - He_incident_dir]
    particle_incident_energies = [He_incident_E]

    particle_parameters = get_particle_parameters(
        Helium,
        particle_starting_positions,
        particle_directions,
        particle_incident_energies,
        N,
    )
    num_chunks = min(N, 10)
    nthreads = 12
    generate_rustbca_input(
        SimID,
        particle_parameters,
        num_chunks,
        nthreads,
        rustbca_input_filename,
        lithium_surface_binding_energy = lithium_surface_binding_energy,
    )



if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1].lower() == 'calibrate':
        format_single_calibration_file(float(sys.argv[2]))
        sys.exit(0)
    main()
