import util
import common
import glob
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

FIG_NUM=0

def plot_iead(iead_datafile, Te_eV, data_set_label, SimLsep, SimID):
    global FIG_NUM
    plt.figure(FIG_NUM)

    IEAD   = np.genfromtxt(iead_datafile,delimiter=' ')
    energy = np.linspace(0.0,24.0*Te_eV,240)
    angles = np.linspace(0,90,90)
    E,A = np.meshgrid(angles,energy)
    plt.contourf(E,A,IEAD)
    plt.xlabel('Angle [deg]')
    plt.ylabel('Energy [eV]')
    plt.ylim([0,50])
    plt.title(f'IEAD for {data_set_label} SOP, Lsep = {SimLsep:.4}m, Te = {Te_eV:.3}eV')

    plt.savefig(
        f'hpic_results/video/iead_{FIG_NUM:02}.png',
        dpi = 300,
    )
    FIG_NUM += 1


def main():
    datafiles = common.DATAFILES
    solps_data = {}
    for data_set_label, datafile in datafiles.items():
        solps_data[data_set_label] = util.load_solps_data(datafile)

    # "minus_0.004m" is logically greater than "minux_0.139" but
    # lexicographically less than it. Achieve logical order by processing
    # globs in chunks.
    chunk1 = sorted(glob.glob('hpic_results/inner_sop_minus*'), reverse = True)
    chunk2 = sorted(glob.glob('hpic_results/inner_sop_plus*'))
    chunk3 = sorted(glob.glob('hpic_results/outer_sop_minus*'), reverse = True)
    chunk4 = sorted(glob.glob('hpic_results/outer_sop_plus*'))
    sims = chunk1 + chunk2 + chunk3 + chunk4
    for SimID in sims:
        # we need to find the electron temperature for the divertor position
        # value associated with this hPIC simulation.
        dataset_for_sim = common.get_dataset_from_SimID(SimID)

        SimLsep = common.get_Lsep_from_SimID(SimID)

        # When the hPIC simulations were configured, Lsep was truncated at
        # 3 decimal points and converted to a string. So we need to go back
        # and inspect the SOLPS data to fiture out which row of data has
        # the closest Lsep value to the one we used for the Simulation ID,
        # i.e. find which was SOLPS data row was used to configure this
        # hPIC simulation in the first place.
        idx = solps_data[dataset_for_sim]['L-Lsep (m)'].searchsorted(SimLsep)
        if idx == len(solps_data[dataset_for_sim]):
            idx -= 1

        # searchsorted returns the index at which WOULD be appropriate to
        # insert the requested value into the array, to preserve order.
        # Since the SOLPS data contains both +/- values, the row we are
        # looking for could be at i-1.
        NextLsep = solps_data[dataset_for_sim].iloc[idx]['L-Lsep (m)']
        PrevLsep =  solps_data[dataset_for_sim].iloc[idx-1]['L-Lsep (m)']

        if abs(NextLsep - SimLsep) < abs(PrevLsep - SimLsep):
            Te_eV = solps_data[dataset_for_sim].iloc[idx]['Te (eV)']
        else:
            Te_eV = solps_data[dataset_for_sim].iloc[idx-1]['Te (eV)']

        iead_datafile = glob.glob(f'{SimID}/*IEAD_sp0.dat')[0]
        plot_iead(iead_datafile, Te_eV, data_set_label, SimLsep, SimID)


if __name__ == '__main__':
    main()

