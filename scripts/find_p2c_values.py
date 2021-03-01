import pandas as pd
import glob
import re

"""
This script is to be fun after hPIC simulations are completed. The assumption
is that the STDOUT of the hPIC simulation was redirected to a log file, and that
the log contains the p2c value (calculated by hPIC). We need the p2c value
for obtaining accurate sputtering yields.
"""


def find_p2c_value(filename):
    """
    Take an hPIC log file and find the p2c value for that simulation.
    """
    with open(filename, 'r') as f:
        for line in f.readlines():
            # capture group only matches the numerical p2c value
            capture_group = '[0-9]{1}\.[0-9]{1,5}e\+[0-9]{1,2}'
            pattern = f'p2c[ ]+ = ({capture_group})[ \t]+Physical-to-Computational ratio'
            match = re.match(pattern, line.strip())
            if match:
                # Expect exactly one such STDOUT log line per hpic simulation.
                # The file still closes even when we call return inside "with"
                # block
                return float(match.groups()[0])

def main():
    p2c_data = {'SimID': [], 'p2c': []}
    simdirs = glob.glob('hpic_results/*')
    for simdir in simdirs:
        SimID =  simdir.replace('hpic_results/', '')
        p2c = find_p2c_value(simdir + '/hpic.log')

        p2c_data['SimID'].append(SimID)
        p2c_data['p2c'].append(p2c)

    df = pd.DataFrame(p2c_data)
    df.to_csv('hpic_results/p2c.csv')

if __name__ == '__main__':
    main()
