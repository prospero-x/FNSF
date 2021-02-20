import pandas as pd
import os
import stat
import yaml
import sys


def get_datafile(keyword):
    if keyword == 'inner':
        return 'solps_data/solpsTargInner.csv'
    elif keyword == 'outer':
        return 'solps_data/solpsTargOuter.csv'
    else:
        print('please specify one if: (inner|outer)')
        sys.exit(1)


def load_yaml(filename):
    with open(filename, 'r') as f:
        y = yaml.load(f, Loader=yaml.FullLoader)
    return y


def load_solps_data(filename, columns_subset = None):
    df = pd.read_csv(
        filename,
        delimiter = ',',
    )
    if columns_subset is None:
        return df
    return df[columns_subset]


def mkdir(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def make_executable(filename):
    os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

