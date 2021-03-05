
"""Store parameters in this file used as arguments to hpic simulations"""
_CONFIG_FILENAME = 'config.yaml'


DATAFILES = {
    'inner': 'solps_data/solpsTargInner.csv',
    'outer': 'solps_data/solpsTargOuter.csv',
}

_MACHINE_ASSIGNMENTS_FILE =  'machine_assignments.yaml'

_PARTICLE_CONVERSION_FACTORS_FILE = 'conversion_factors.csv'

_columns_of_interest = [
    'L-Lsep (m)',
    #'R (m)',
    #'Z (m)',
    'Te (eV)',
    'Ti (eV)',
    #'FluxLi+3',
    #'FluxLi+2',
    #'FluxLi+1',
    #'FluxNe+10',
    #'FluxNe+9',
    #'FluxNe+8',
    #'FluxNe+7',
    #'FluxNe+6',
    #'FluxNe+5',
    #'FluxNe+4',
    #'FluxNe+3',
    #'FluxNe+2',
    #'FluxNe+1',
    #'FluxD+1',
    #'nLi+3',
    #'nLi+2',
    #'nLi+1',
    'nNe+10',
    'nNe+9',
    'nNe+8',
    'nNe+7',
    'nNe+6',
    'nNe+5',
    'nNe+4',
    'nNe+3',
    'nNe+2',
    'nNe+1',
    'nD+1',
    '|B| (T)',
    'Bangle (deg)',
    #'q_e (W/m2)',
    #'q_i (W/m2)',
    #'q_tot (W/m2)',
]

# Each ion with it charge number and (average) atomic mass
_ions_of_interest = {
    'nD+1':   {'Ai': 2.014,   'Zi': 1,  'qi': 1},
    'nNe+1':  {'Ai': 20.1797, 'Zi': 1, 'qi': 1},
    'nNe+2':  {'Ai': 20.1797, 'Zi': 2, 'qi': 2},
    'nNe+3':  {'Ai': 20.1797, 'Zi': 3, 'qi': 3},
    'nNe+4':  {'Ai': 20.1797, 'Zi': 4, 'qi': 4},
    'nNe+5':  {'Ai': 20.1797, 'Zi': 5, 'qi': 5},
    'nNe+6':  {'Ai': 20.1797, 'Zi': 6, 'qi': 6},
    'nNe+7':  {'Ai': 20.1797, 'Zi': 7, 'qi': 7},
    'nNe+8':  {'Ai': 20.1797, 'Zi': 8, 'qi': 8},
    'nNe+9':  {'Ai': 20.1797, 'Zi': 9, 'qi': 9},
    'nNe+10': {'Ai': 20.1797, 'Zi': 10, 'qi': 10},
}


_all_ions = [
    'nLi+3',
    'nLi+2',
    'nLi+1',
    'nNe+10',
    'nNe+9',
    'nNe+8',
    'nNe+7',
    'nNe+6',
    'nNe+5',
    'nNe+4',
    'nNe+3',
    'nNe+2',
    'nNe+1',
    'nD+1',
]

def get_data_set_label(datafile):
    data_set_label = datafile.split('/')[-1].split('.')[0]
    _labels = {
        'solpsTargInner': 'Inner SOP',
        'solpsTargOuter': 'Outer SOP',
    }
    return _labels[data_set_label]


import re

def get_dataset_from_SimID(SimID):
    """
        Example: SimID: outer_sop_minus_0.002m_from_sp
            returns: 'outer'
    """
    try:
        dataset = re.search('(outer|inner)', SimID).group()
    except AttributeError:
        breakpoint()
    return dataset


def get_Lsep_from_SimID(SimID):
    """
    Example: SimID: outer_sop_minus_0.002m_from_sp
        returns: -0.002
    """
    Lsep_str = re.search('(plus|minus)_[0-9].[0-9]{1,3}', SimID).group()
    sign, val = Lsep_str.split('_')
    sign = 1 if sign == 'plus' else -1
    return sign * float(val)

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


