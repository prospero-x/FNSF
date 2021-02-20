import sys
from common import _all_ions
import util
import common
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt


"""
This script is meant to be used for a preliminary view of the SOLPS data.
Densities of each ion are plotted as as fraction of the total.
"""

def plot_densities(df, data_set_label):
    _, ax = plt.subplots(figsize=(12,10))
    ax.tick_params(axis = 'both', which = 'major', labelsize = 20)
    ax.tick_params(axis = 'both', which = 'minor', labelsize = 20)


    # First column holds L-Lsep
    linestyles = ['-','--']
    top_ions = set(['nD+1', 'nNe+1', 'nNe+2', 'nNe+3'])
    i = 0
    for ion in df.columns[1:]:
        linewidth = 3 if ion in top_ions else 1
        ax.semilogy(
            df['L-Lsep (m)'],
            df[ion],
            linestyle = linestyles[i%2],
            linewidth = linewidth,
            marker = '.',
            label = ion[1:],
        )
        i += 1

    plt.ylabel('n (m$^{-3}$)', fontsize = 20)
    plt.xlabel('L-Lsep (m)', fontsize = 20)
    plt.legend(prop=dict(size=16), ncol=3)
    plt.title(data_set_label +' Ion Densities', fontsize = 24)
    plt.ylim(top = 1e27)
    plt.show()


def main():
    if len(sys.argv) < 2:
        print('usage: $python compute_ion_gyroradii.py (inner|outer)')
        return
    datafile_keyword = sys.argv[1]
    datafile = util.get_datafile(datafile_keyword)
    data_set_label = common.get_data_set_label(datafile)

    columns = ['L-Lsep (m)'] + _all_ions
    df = util.load_solps_data(datafile, columns_subset = columns)
    plot_densities(df, data_set_label)

if __name__ == '__main__':
    main()
