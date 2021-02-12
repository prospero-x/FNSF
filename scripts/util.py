import pandas as pd
import os
import stat
from columns import _columns_of_interest


def load_solps_data(filename):
    df = pd.read_csv(
        filename,
        delimiter = ',',
    )
    return df[_columns_of_interest]


def mkdir(dirname):
    if not os.path.exists(dirname):
        os.mkdir(dirname)


def make_executable(filename):
    os.chmod(filename, stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

