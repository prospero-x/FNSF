import numpy as np
import os
import toml
import util


C = 2.99792458E8
C2 = C**2
QE = 1.602176634E-19
AMU = 1.67377E-27
MICRON = 1E-6

"""
This script is used to generate input files for RustBCA simulations.

After running this script, one directory for each energy is created, and in
each directory a subdirectory for each y-offset is created. Inside each
subdirectory, an input.toml file is created for RustBCA to use.
"""



def get_starshot_height_and_length():
    """
    :return: starshot height and length, in microns. The length
        is the direction tangent to the spacecraft's velocity
    """
    return 1.0, 10.0


def rotate(X, theta):
    """
    Rotate a 2D vector by angle theta.
    """
    Xprime = np.copy(X)
    Xprime[0] = X[0] * np.cos(theta) - X[1] * np.sin(theta)
    Xprime[1] = X[0] * np.sin(theta) + X[1] * np.cos(theta)
    return Xprime


def get_starshot_spacecraft_boundary_points():
    """
    Rotate, so we don't run into the gimball lock problem of RustBCA
    """
    height, length = get_starshot_height_and_length()
    theta = 0.0
    b1 = rotate((0., height/2.), theta)
    b2 = rotate((0., -height/2.), theta)
    b3 = rotate((length, height/2.), theta)
    b4 = rotate((length, -height/2.), theta)
    return b1, b2, b3, b4


def get_simulation_boundary_points():
    """
    The simulation area will be the same shape as the starshot
    boundary points, just extended slightly in each direction.
    """
    height, length = get_starshot_height_and_length()
    b1, b2, b3, b4 = get_starshot_spacecraft_boundary_points()
    broadening_factor = 0.05
    sb1 = (b1[0] - length * broadening_factor, b1[1] + height * broadening_factor)
    sb2 = (b2[0] - length * broadening_factor, b2[1] - height * broadening_factor)
    sb3 = (b3[0] + length * broadening_factor, b3[1] + height * broadening_factor)
    sb4 = (b4[0] + length * broadening_factor, b4[1] - height * broadening_factor)
    return sb1, sb2, sb3, sb4


def initial_particle_direction():
    """
    :return: inital direction of incident Fe ions. This is orthogonal
        to the front of the spacecraft, tangent to the spacecraft's
        direction of travel
    """
    b1, _, b3, _ = get_starshot_spacecraft_boundary_points()
    direction = b3[0] - b1[0], b3[1] - b1[1], 0.

    # rotate a tiny tiny bit to avoid gimball lock
    theta = 1e-3
    rotated = rotate(direction, theta)
    norm = np.sqrt(np.dot(rotated, rotated))
    return rotated/norm


def get_starshot_mesh_coordinate_sets():
    b1, b2, b3, b4 = get_starshot_spacecraft_boundary_points()
    triangle1 = [b2[0], b1[0], b3[0], b2[1], b1[1], b3[1]]
    triangle2 = [b2[0], b4[0], b3[0], b2[1], b4[1], b3[1]]
    return triangle1, triangle2



def generate_rustbca_input(name, N_incident, incident_energies, incident_angles, input_filename):

    options = {
        'name': name,
        'track_trajectories': True,
        'track_recoils': True,
        'track_displacements': True,
        'track_energy_losses': True,
        'track_recoil_trajectories': True,
        'stream_size': 8000,
        'weak_collision_order': 0,
        'suppress_deep_recoils': False,
        'high_energy_free_flight_paths': False,
        'num_threads': 8,
        'num_chunks': min(10, N_incident),
        'use_hdf5': False,
        'electronic_stopping_mode': 'INTERPOLATED',
        'mean_free_path_model': 'LIQUID',
        'interaction_potential': [['KR_C']],
    }

    """
    Target Material (Lithium) properties (values from ./materials_info.txt)
    """
    # Density (atoms per cubic micron)
    n_target = 4.633e+10

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
        'electronic_stopping_correction_factor': 1.0,
        'surface_binding_model': "AVERAGE"
    }

    height, length = get_starshot_height_and_length()
    energy_barrier_thickness = (n_target)**(-1./3.)/np.sqrt(2.*np.pi)

    starshot_boundary_points = get_starshot_spacecraft_boundary_points()

    mesh_2d_input = {
        'length_unit': 'MICRON',
        'coordinate_sets': get_starshot_mesh_coordinate_sets(),
        'densities': [[n_target], [n_target]],
        'boundary_points': starshot_boundary_points,
        'simulation_boundary_points': get_simulation_boundary_points(),
        'energy_barrier_thickness': energy_barrier_thickness,
    }

    """
    Incident ion properties
    """
    # Average Mass (a.m.u.)
    m_incident = 2.014

    # Proton Count
    Z_incident = 1

    # Cutoff energy of incident ions (eV)
    Ec_incident = 0.95

    # Surface binding energy of incident ions (eV)
    Es_incident = 1.5
    M = len(incident_energies)
    particle_parameters = {
        'length_unit': 'MICRON',
        'energy_unit': 'EV',
        'mass_unit': 'AMU',
        'N': [N] * M,
        'm': [m_incident] * M,
        'Z': [Z_incident] * M,
        'E': incident_energies,
        'Ec': [Ec_incident]*M ,
        'Es': [Es_incident]*M,
        'interaction_index': [0],
        'pos': [[0.0, 0.0, 0.0]]*M,
        'dir': incident_angles,
        'particle_input_filename': ''
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
        f.write(r'scattering_integral = [[{"GAUSS_MEHLER"={n_points = 10}}]]')
        f.write('\n')
        f.write(r'root_finder = [[{"NEWTON"={max_iterations = 100, tolerance=1E-3}}]]')


def relativistic_kinetic_energy(m, v):
    """
    Compute the relatvistiv kinetic energy of a fast-moving
    particle

    :param m: mass of particle, in kg
    :param v: velocity of particle, in m/s
    :return: kinetic energy of particle, in eV
    """
    lorentz_factor = 1/np.sqrt(1 - v**2/C2)
    Ek = (lorentz_factor - 1)*m*C2
    return Ek / QE


def get_ion_energies():
    return np.linspace(0, 10, 3)


def get_ion_incident_angles():
    return np.linspace(0, 90, 10)


if __name__ == '__main__':
    ion_energies = get_ion_energies()
    ion_incident_angles = get_ion_incident_angles()


    output_dir = 'rustbca_results'
    util.mkdir(output_dir)

    rustbca_input_file = output_dir + '/example_input.toml'

    N = 10
    generate_rustbca_input(
        'this-is-a-test',
        N,
        ion_energies,
        ion_incident_angles,
        rustbca_input_file,
    )
