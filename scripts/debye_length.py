from common import _all_ions, get_data_set_label
import util
import sys
import scientific_constants as sc
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd


def compute_debye_length_for_row(df_row):
    """
    return the debye length for a row in meters.
    """
    # Assumption: the electron density is equal to the sum of
    # all lithium, neon, and deuterium ion densities.
    ne = df_row['nD+1']

    Te = df_row['Te (eV)']

    # Compute the debye length [m]
    debye_length = np.sqrt(sc.eps0 * Te / (sc.qe * ne))
    return debye_length


def compute_debye_lengths(df):
    """
    return a 2-column np array. column 1 = Lsep, column2 = debye length (m)
    """
    D = np.zeros((len(df), 2))
    for n, row in df.iterrows():
        Lsep = row['L-Lsep (m)']
        debye_length = compute_debye_length_for_row(row)

        D[n][0] = Lsep
        D[n][1] = debye_length

    # Convert to a Dataframe for named columns
    columns = ['L-Lsep (m)', 'Debye Length (m)']
    D = pd.DataFrame(data = D, columns = columns)
    return D


def plot_debye_lengths(debye_lengths, data_label):
    _, ax = plt.subplots(figsize=(12,10))
    ax.tick_params(axis = 'both', which = 'major', labelsize = 16)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 16)


    plt.semilogy(
        debye_lengths['L-Lsep (m)'],
        debye_lengths['Debye Length (m)'],
        '.-',
    )
    plt.ylabel('Debye Length (m)', fontsize = 16)
    plt.xlabel('L-Lsep (m)', fontsize = 16)
    plt.title(data_label + ' Debye Lengths', fontsize = 24)
    plt.show()


def main():
    if len(sys.argv) < 2:
        print('usage: python compute_debye_lengths.py (inner|outer)')
        return

    datafile = util.get_datafile(sys.argv[1])
    data_label = get_data_set_label(datafile)
    df = util.load_solps_data(datafile)
    debye_lengths = compute_debye_lengths(df)
    plot_debye_lengths(debye_lengths, data_label)


if __name__ == '__main__':
    main()
