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

def get_target_height_and_length():
    """
    :return: target height and length, in microns.
    """
    return 1.0, 1.0


def rotate(X, theta):
    """
    Rotate a 2D vector by angle theta.
    """
    Xprime = np.copy(X)
    Xprime[0] = X[0] * np.cos(theta) - X[1] * np.sin(theta)
    Xprime[1] = X[0] * np.sin(theta) + X[1] * np.cos(theta)
    return Xprime


def get_target_boundary_points(height, length, theta = 0.0):
    b1 = rotate((-length/2., 0), theta)
    b2 = rotate((-length/2., -height), theta)
    b3 = rotate((length/2., 0), theta)
    b4 = rotate((length/2., -height), theta)
    return b1, b2, b3, b4


def get_simulation_boundary_points(broadening_factor = 0.05):
    height, length = get_target_height_and_length()
    b1, b2, b3, b4 = get_target_boundary_points(height, length)
    sb1 = (b1[0] - length * broadening_factor, b1[1] + height * broadening_factor)
    sb2 = (b2[0] - length * broadening_factor, b2[1] - height * broadening_factor)
    sb3 = (b3[0] + length * broadening_factor, b3[1] + height * broadening_factor)
    sb4 = (b4[0] + length * broadening_factor, b4[1] - height * broadening_factor)
    return sb1, sb2, sb3, sb4


def get_target_mesh_triangles(height, length):
    b1, b2, b3, b4 = get_target_boundary_points(height, length)
    triangle1 = [b2[0], b1[0], b3[0], b2[1], b1[1], b3[1]]
    triangle2 = [b2[0], b4[0], b3[0], b2[1], b4[1], b3[1]]
    return triangle1, triangle2



def generate_rustbca_input(
    name,
    particle_parameters,
    num_chunks,
    input_filename):

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
        'num_threads': 12,
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

    # Surface Binding Energy (eV)
    Es_target = 1.64

    # Bulk Binding Energy (eV)
    Eb_target = 1.64

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
        'Es': [Es_target],
        'Ec': [Ec_target],
        'Z': [Z_target],
        'm': [m_target] ,
        'interaction_index': [0],
        'surface_binding_model': "AVERAGE"
    }

    height, length = get_target_height_and_length()
    energy_barrier_thickness = n_target**(-1./3.)

    target_boundary_points = get_target_boundary_points(height, length)
    triangles = get_target_mesh_triangles(height, length)
    mesh_2d_input = {
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
        'mesh_2d_input': mesh_2d_input,
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
    'mass': 2.014,  # Average Mass (a.m.u.)
    'Z':  1,  # Proton Count
    'Ec': 0.95,  # Cutoff energy, eV
    'Es': 1.5,  # Surface Binding Energy, eV
}


def angle_to_dir(angle):
    """
    take: scalar angle value, which represents a normal to the divertor
    return: a three-tuple, representing the x, y, and z direction
    """
    radians = angle * np.pi / 180
    particle_dir = np.array([np.sin(radians), -np.cos(radians), 0.0])
    return np.round(particle_dir, decimals = 5)


def get_particle_parameters(
        IEAD,
        Te,
        material,
        particle_starting_positions,
        particle_directions,
        example = False,
        factor = 1.0):
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
        'm': [material['mass']] * M ,
        'Z': [material['Z']] * M,
        'E': incident_energies,
        'Ec': [material['Ec']] * M,
        'Es': [material['Es']]*M,
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
        keys_with_large_values = ['E', 'N', 'm', 'Z', 'Ec', 'Es', 'pos', 'dir']
        for k in keys_with_large_values:
            del particle_parameters[k]
    return particle_parameters


def invert_ion_map(ion_map):
    """
    @param: ion_map: list of dictionaries where keys are ion names and values
         are hpic labels
    @return: dictionary where keys are hpic lables and keys are ion names
    """
    rv = {}
    for i, ion_info in enumerate(ion_map):
        ion_name = list(ion_info.keys())[0]
        rv[f'sp{i}'] = ion_name
    return rv


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
    example = False
    if len(sys.argv) == 2:
        if sys.argv[1].lower() != 'example':
            print('usage: python build_rustbca_input_files.py [example]')
            sys.exit(1)
        else:
            example = True


    # Pin down species names in a config file so we're never wondering what
    # ion "sp4" is.
    config = util.load_yaml(common._CONFIG_FILENAME)
    ion_names = invert_ion_map(config['ions'])

    output_dir = 'rustbca_simulations'
    if example:
        output_dir = 'rustbca_simulation_examples'
    util.mkdir(output_dir)

    datafiles = common.DATAFILES
    solps_data = {}
    for data_set_label, datafile in datafiles.items():
        solps_data[data_set_label] = util.load_solps_data(datafile)


    # Initialize directions head of time. This is based on the assumptino that
    # the IEAD has 240 rows (240 energies ranging from 0 to 24*Te) and 90
    # columns (one for each angle between 0 and 90)
    particle_directions = []
    particle_starting_positions = []

    directions = [angle_to_dir(x) for x in range(90)]
    N_e = 240
    for _ in range(N_e):
        for theta in range(90):
            particle_directions.append(directions[theta])
            particle_starting_positions.append(-1 * directions[theta])

    for SimID in glob.glob('hpic_results/*'):
        dataset_for_sim = common.get_dataset_from_SimID(SimID)
        SimLsep = common.get_Lsep_from_SimID(SimID)
        Te = get_Te_for_Lsep(SimLsep, solps_data[dataset_for_sim])

        for IEADfile in glob.glob(SimID + '/*_IEAD_*.dat'):
            # Get this species name
            iead_label = re.search('IEAD_sp[0-9]{1,2}', IEADfile).group()
            species_label = iead_label.split('_')[1]
            ion_name = ion_names[species_label]

            IEAD = np.genfromtxt(IEADfile, delimiter = ' ')
            particle_parameters = get_particle_parameters(
                IEAD,
                Te,
                Deuterium,
                particle_starting_positions,
                particle_directions,
                example = example,
            )

            RustBCA_SimID = SimID.replace('hpic_results/', '')
            rustbca_input_file = output_dir + '/' + RustBCA_SimID + '.toml'
            num_chunks = 100

            generate_rustbca_input(
                RustBCA_SimID,
                particle_parameters,
                num_chunks,
                rustbca_input_file,
            )

if __name__ == '__main__':
    main()
