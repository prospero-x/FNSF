import glob
import numpy as np
import util
import common
import re
import toml

"""
This is a sanity check script. Each RustBCA simulation is created from an IEAD data file.
Sometimes we multiply each number in that file in order to get to a minimum threshold
to be considered a "high resolution" simulation. This script verifies that the total
number of particles in a RustBCA input file equals the total number in the associated
IEAD file times the corresponding conversion factor found in conversion_factors.csv.
"""

def get_conversion_factors():
    factors = {}
    with open(common._PARTICLE_CONVERSION_FACTORS_FILE, 'r') as f:
        for line in f.readlines():
            rustbca_simdir, factor = line.strip().split(',')
            factors[rustbca_simdir] = float(factor)
    return factors


def get_rustbca_simulation_counts():
    counts = {}
    for rustbca_simdir in glob.glob('rustbca_simulations/*'):
        rustbca_input_file = rustbca_simdir + '/input.toml'
        print(f'reading {rustbca_input_file}...')
        with open(rustbca_input_file, 'r') as f:
            rustbca_config = toml.load(f)
        counts[rustbca_simdir + '/'] = sum(rustbca_config['particle_parameters']['N'])
    return counts


def verify_particle_counts():
    IEAD_counts = get_IEAD_counts()
    conversion_factors = get_conversion_factors()
    rustbca_counts = get_rustbca_simulation_counts()

    for rustbca_simdir, rustbca_count in rustbca_counts.items():
        IEAD_count = IEAD_counts[rustbca_simdir]
        conversion_factor = conversion_factors[rustbca_simdir]
        assert rustbca_count == IEAD_count * conversion_factor
    print('all particle counts make sense ✔')


def get_IEAD_counts():
    counts = {}
    # ping down species names in a config file so we're never wondering what
    # ion "sp4" is.
    config = util.load_yaml(common._CONFIG_FILENAME)
    ion_names = common.invert_ion_map(config['ions'])

    for SimID in glob.glob('hpic_results/*'):
        if SimID == 'hpic_results/p2c.csv':
            continue


        for IEADfile in glob.glob(SimID + '/*_IEAD_*.dat'):
            # Get this species name
            iead_label = re.search('IEAD_sp[0-9]{1,2}', IEADfile).group()
            species_label = iead_label.split('_')[1]
            ion_name = ion_names[species_label]

            IEAD = np.genfromtxt(IEADfile, delimiter = ' ')
            RustBCA_Simdir = 'rustbca_simulations/' + SimID.replace('hpic_results/', '') + ion_name + '/'
            counts[RustBCA_Simdir] = np.sum(IEAD)

    return counts


if __name__ == '__main__':
    verify_particle_counts()
