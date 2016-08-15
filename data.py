""" Methods for processing data in DEBUT analysis

Included methods:
"""

import glob
import numpy as np, pandas as pd


dname='/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/prepped_data/'
def load(nrows=None):
    """Load prepped data from /home/J/LIMITED_USE

    Parameters
    ----------
    nrows : int, optional
      For faster processing, load only the first 1,000 rows from each
      year.

    Results
    -------
    returns a pd.DataFrame with columns code_seq, date_seq, and emrg_seq
    """

    df_dict = {}
    for fname in sorted(glob.glob(dname + '20*.csv')):
        t = pd.read_csv(fname, nrows=nrows, index_col='id')
        y = t.year.iloc[0]
        assert np.all(t.year == y)
        df_dict[y] = t

    # merge code sequence and every surgery for all years for these patients
    t = df_dict[2007]

    code_seq = t.code_seq.fillna('')
    date_seq = t.date_seq.fillna('')
    emrg_seq = t.emrg_seq.fillna('')

    for y in range(2008, 2015):
        t = df_dict[y]

        code_seq += ' '
        code_seq = code_seq.add(t.code_seq, fill_value='')
    
        date_seq += ' '
        date_seq = date_seq.add(t.date_seq, fill_value='')

        emrg_seq += ' '
        emrg_seq = emrg_seq.add(t.emrg_seq, fill_value='')
    
    code_seq = code_seq.fillna('')
    date_seq = date_seq.fillna('')
    emrg_seq = emrg_seq.fillna('')

    return pd.DataFrame({'code_seq': code_seq,
                         'date_seq': date_seq,
                         'emrg_seq': emrg_seq,})

