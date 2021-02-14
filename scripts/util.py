import pandas as pd
import os
import stat


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

def get_data_set_label(datafile):
    data_set_label = datafile.split('/')[-1].split('.')[0]
    _labels = {
        'solpsTargInner': 'Inner Strike Point',
        'solpsTargOuter': 'Outer Strike Point',
    }
    return _labels[data_set_label]

