import util
import common
import glob
import numpy as np
import scientific_constants as sc
import pandas as pd
from collections import defaultdict
import matplotlib.pyplot as plt
import os
import sys

# These are the values for Lithium surface binding energy
# which were used in rustbca simulations. The results must
# be distinguished by the SBE used in the simulation config.
SBEs = [
    '1eV',
    '4eV',
]


def energy_to_velocity(E, m):
    """
    @param E: kinetic energy in eV
    @param m: mass in AMU

    @returns: velocity in m/s
    """
    E_joules = E * sc.qe
    m_kg = m * sc.amu2kg
    return np.sqrt(E_joules * 2 / m_kg)


def get_conversion_factors(ion_name):
    factors = {}
    with open(f'rustbca_conversion_factors/{ion_name}.csv') as f:
        for line in f.readlines():
            rustbca_dir, factor = line.strip().split(',')
            SimID = rustbca_dir.split('/')[1].split('from_sp')[0] + 'from_sp'
            factors[SimID] = float(factor)

    return factors

def get_simulation_times():
    total_times = {}
    with open('simulation_times.csv', 'r') as f:
        for line in f.readlines():
            SimID, p2c = line.split(',')
            total_times[SimID] = float(p2c)

    return total_times


def get_p2c_coefficients():
    p2c_coefficients = {}
    with open('hpic_results/p2c.csv', 'r') as f:
        f.readline()
        for line in f.readlines():
            n, SimID, p2c = line.split(',')
            p2c_coefficients[SimID] = float(p2c)

    return p2c_coefficients


def physical_sputtering(ion_name, hpic_ion_label):
    conversion_factors = get_conversion_factors(ion_name)
    p2c_coefficients = get_p2c_coefficients()
    simulation_times = get_simulation_times()

    # Load solps data so we can look up various ion densities
    solps_data = {}
    for data_set_label, datafile in common.DATAFILES.items():
        solps_data[data_set_label] = util.load_solps_data(datafile)

    df_data = defaultdict(list)
    for SBE_dir in glob.glob('rustbca_simulations/SBE*'):
        for rustbca_simdir in glob.glob(SBE_dir + f'/*{ion_name}'):
            SimID = rustbca_simdir.split('/')[-1].split('from_sp')[0] + 'from_sp'
            ion_name = rustbca_simdir.split('/')[-1].split('from_sp')[1]

            sputtered_datafile = rustbca_simdir + '/sputtered.output'
            if os.path.exists(sputtered_datafile) and os.path.getsize(sputtered_datafile):
                Nsput = np.size(np.genfromtxt(sputtered_datafile, delimiter = ','))
            else:
                Nsput = 0

            dataset_for_sim = common.get_dataset_from_SimID(SimID)
            SimLsep = common.get_Lsep_from_SimID(SimID)

            Nincident = np.sum(np.genfromtxt(
                f'hpic_results/{SimID}/{SimID}_IEAD_{hpic_ion_label}.dat',
            ))

            p2c = p2c_coefficients[SimID]
            sim_time = simulation_times[SimID]
            try:
                conversion_factor = conversion_factors[SimID]
            except KeyError:
                breakpoint()

            SBE = SBE_dir.split('_')[-1]

            df_data['p2c'].append(p2c)
            df_data['rustbca_conversion_factor'].append(conversion_factor)
            df_data['Nsput'].append(Nsput)
            df_data['strike_point'].append(dataset_for_sim)
            df_data['Li-SBE (eV)'].append(SBE)
            df_data['L-Lsep (m)'].append(SimLsep)
            df_data['simulation time'].append(sim_time)
            df_data['Nincident'].append(Nincident)
            df_data['sputtering_yield'].append(Nsput / conversion_factor / Nincident)
            df_data['gamma'].append(Nsput * p2c / sim_time / conversion_factor)

    df = pd.DataFrame(data = df_data)
    return df


def get_density_for_Lsep(Lsep, df, ion_name):
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
        density = df.iloc[idx][ion_name]
    else:
        density = df.iloc[idx-1][ion_name]
    return density

def plot_sputtered_gamma(df, ion_name, strike_point_label):
    """
    Y-axis: gamma (sputtered particles per meter square per second
    X-Axis: L-Lsep (m)
    """
    _, ax = plt.subplots(figsize=(12,10))
    ax.tick_params(axis = 'both', which = 'major', labelsize = 16)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 16)

    for SBE in SBEs:
        df = df[df['Li-SBE (eV)'] == SBE]
        if df.empty:
            continue
        ax.semilogy(
            df['L-Lsep (m)'],
            df['gamma'],
            'r.',
            label = f'Li SBE = {SBE}',
            markersize = 12,
        )

    plt.ylabel('$\\Gamma$ (m$^{-2}$ s$^{-1}$)', fontsize = 20)
    plt.xlabel('L-Lsep (m)', fontsize = 20)
    plt.legend(prop=dict(size=20))
    plt.title(
        f'Liquid Lithium Sputtered Flux from {ion_name} Impacts\n'
        + f'({strike_point_label.title()} Strike Point)',
        fontsize = 24,
    )
    plt.show()


def plot_sputtering_yields(df, ion_name, strike_point_label):
    """
    Y-axis: Y (ratio of sputtered to incident particles)
    X-Axis: L-Lsep (m)
    """
    _, ax = plt.subplots(figsize=(12,10))
    ax.tick_params(axis = 'both', which = 'major', labelsize = 16)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 16)

    for SBE in SBEs:
        df_for_SBE = df[df['Li-SBE (eV)'] == SBE]
        if not df_for_SBE:
            continue
        ax.scatter(
            df_for_SBE['L-Lsep (m)'],
            df_for_SBE['sputtering_yield'],
            s = 40,
            label = f'Li SBE = {SBE}',
        )

    plt.ylabel('$Y_{sput}$', fontsize = 16)
    plt.xlabel('L-Lsep (m)', fontsize = 16)
    plt.legend(prop=dict(size=16))
    plt.title(
        f'Liquid Lithium Sputtering Yield from {ion_name} Impacts\n'
        + f'({strike_point_label.title()} Strike Point)',
        fontsize = 24,
    )
    plt.show()

if __name__ == '__main__':

    config = util.load_yaml(common._CONFIG_FILENAME)
    ion_map = common.ion_map(config['ions'])
    ions = [
        #'nD+1',
        #'nNe+1',
    ]
    ions = [sys.argv[1]]
    for ion_name in ions:
        sputtered = physical_sputtering(ion_name, ion_map[ion_name])
        for strike_point_label in ['inner', 'outer']:
            df = sputtered[(sputtered['strike_point'] == strike_point_label)]
            plot_sputtered_gamma(df, ion_name, strike_point_label)
            #plot_sputtering_yields(df, ion_name, strike_point_label)
