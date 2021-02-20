import sys
from common import _columns_of_interest, _ions_of_interest
import util
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import scientific_constants as sc


"""
This script is meant to be a sanity check on the SOLPS data. We want
to calculate the gyroradius of the incoming ions to make sure they're
not intersecting the diverter before the strike point.
"""

Qe = 1.602176e-19


# 1 Dalton [kg]
amu2kg = 1.6605e-27


# Boltzmann Constant [J/K]
kB = 1.380649e-23


def gyroradius_for_row(df_row):
    """
    Calculate the gyroradius given a row (i.e. a LOCATION) at the divertor.

    Since all other ions have a low density compared to deuterium, we consider
    ONLY the deuterium mass/charge when determining the gyroradius.

    :param: df_row: a single row in the SOLPS output data.
    :returns: gyroradius, in meters
    """

    B0 = df_row['|B| (T)']
    Ti = df_row['Ti (eV)']

    dt_ion_info = _ions_of_interest['nD+1']
    A_D = dt_ion_info['Ai']
    q_D = dt_ion_info['qi'] * sc.qe
    m_D = A_D * sc.amu2kg

    # Since all other ions have a low density compared to deuterium,
    # consider ONLY the deuterium mass/charge to determine the gyroradius.
    rg = gyroradius(Ti, m_D, q_D, B0)
    return rg


def gyroradius(T, m, q, B):
    """
    Calculate the gyroradius of a species in the tokamak.

    To compute v_parallel, use the mean velocity formula: sqrt(8/pi * kT/m)

    :param: T: ion temperature, in eV
    :param: m: ion mass, in kg
    :param: q: ion charge, in Coulombs
    :param: B: B field strength, in Tesla

    :returns: gyroradius, in meters
    """
    v = np.sqrt(8./np.pi * Qe * T / m)
    rg = m * v / q / B
    return rg


def compute_gyroradii(df):
    N = len(df)
    M = len(_ions_of_interest)

    # Matrix to hold the gyroradii
    Rg = np.zeros((N, M + 1))

    # Matrix to hold the errors
    dX = np.zeros((N, M + 1))

    ions = sorted(_ions_of_interest.keys())

    for n, row in df.iterrows():
        Lsep = row['L-Lsep (m)']
        B0 = row['|B| (T)']
        phi = row['Bangle (deg)']
        Ti = row['Ti (eV)']

        # The first column holds the x-position
        Rg[n][0] = Lsep
        dX[n][0] = Lsep

        m = 1

        for ion in ions:
            ion_info = _ions_of_interest[ion]
            Ai = ion_info['Ai']
            Zi = ion_info['Zi']
            qi = ion_info['qi'] * Qe

            mi = Ai * amu2kg

            rg = gyroradius(Ti, mi, qi, B0)
            Rg[n][m] = rg

            delta_x = rg / np.sin(np.pi/2 - phi*np.pi/180)
            dX[n][m] = delta_x
            m += 1

    # Create pandas DFs so we can refer to columns by header
    columns = ['L-Lsep (m)'] + [x.replace('n','') for x in ions]
    Rg = pd.DataFrame(data = Rg, columns = columns)
    dX = pd.DataFrame(data = dX, columns = columns)
    return Rg, dX


def plot_gyroradii(Rg, data_set_label):
    _, ax = plt.subplots(figsize=(12,10))
    ax.tick_params(axis = 'both', which = 'major', labelsize = 16)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 16)


    # First column holds L-Lsep
    for ion in Rg.columns[1:]:
        ax.semilogy(Rg['L-Lsep (m)'], Rg[ion], '.-', label = ion)

    plt.ylabel('gyroradius (m)', fontsize = 16)
    plt.xlabel('L-Lsep (m)', fontsize = 16)
    plt.legend(prop=dict(size=16), ncol=3)
    plt.title(data_set_label +' gyroradii', fontsize = 24)
    plt.show()



def plot_dX(dX, data_set_label):
    _, ax = plt.subplots(figsize=(12,10))
    ax.tick_params(axis = 'both', which = 'major', labelsize = 16)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 16)


    # First column holds L-Lsep
    for ion in dX.columns[1:]:
        ax.semilogy(dX['L-Lsep (m)'], dX[ion], '.-', label = ion)

    plt.ylabel('$\\delta x$ (m)', fontsize = 16)
    plt.xlabel('L-Lsep (m)', fontsize = 16)
    plt.legend(prop=dict(size=16), ncol=3)
    plt.title(data_set_label +'Intersection Error $\\delta x$', fontsize = 24)
    plt.show()


def main():
    if len(sys.argv) < 2:
        print('usage: $python compute_ion_gyroradii.py (inner|outer )')
        return
    datafile_keyword = sys.argv[1]
    datafile = util.get_datafile(datafile_keyword)
    data_set_label = util.get_data_set_label(datafile)
    df = util.load_solps_data(datafile, columns_subset = _columns_of_interest)
    Rg, dX = compute_gyroradii(df)
    plot_gyroradii(Rg, data_set_label)
    plot_dX(dX, data_set_label)

if __name__ == '__main__':
    main()
