""" Methods for processing data in DEBUT analysis

Included methods:
  load
  is_included
  surgery_for_cancer
  emergency_surgery
  included_subjects
  seqs_dur_exposure_period
  days_until_surgery
  clipped_labeled_sequences
"""

import glob
import numpy as np, pandas as pd


dname='/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/prepped_data/'
df_dict = {}

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
    global df_dict
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
    in_seq = t.in_seq.fillna('')
    pay_seq = t.pay_seq.fillna('')

    for y in range(2008, 2015):
        t = df_dict[y]

        code_seq += ' '
        code_seq = code_seq.add(t.code_seq, fill_value='')
    
        date_seq += ' '
        date_seq = date_seq.add(t.date_seq, fill_value='')

        emrg_seq += ' '
        emrg_seq = emrg_seq.add(t.emrg_seq, fill_value='')

        in_seq += ' '
        in_seq = in_seq.add(t.in_seq, fill_value='')

        pay_seq += ' '
        pay_seq = pay_seq.add(t.pay_seq, fill_value='')
    
    code_seq = code_seq.fillna('')
    date_seq = date_seq.fillna('')
    emrg_seq = emrg_seq.fillna('')
    in_seq = in_seq.fillna('')
    pay_seq = pay_seq.fillna('')

    return pd.DataFrame({'code_seq': code_seq,
                         'date_seq': date_seq,
                         'emrg_seq': emrg_seq,
                         'in_seq': in_seq,
                         'pay_seq': pay_seq,
                        })


### setup lists of important icd and cpt codes

colonic_dvt_codes = '56211 56213'.split()
# need to prepend icd9 to the cause list
colonic_dvt_codes = ['icd9-'+c for c in colonic_dvt_codes]

# Using the MarketScan Commercial Claims database (Truven Health Analytics),
# we selected all adult patients with a new diagnosis of diverticulitis
# and two years of continuous enrollment before and after the year of diagnosis

def is_included(df, id):
    """test if a patient is included according to the criteria of
    continuous enrollment for two years before and after the year of
    diagnosis

    Parameters
    ----------
    df : pd.DataFrame, with columns code_seq and date_seq
    id : int, patient id

    Results
    -------
    returns bool, True iff continuously enrolled for two years before
    and after year of diagnosis
    """

    global df_dict

    cs = pd.Series(df.code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) == 0:
        return False  # no dx, should not be in cohort
    
    ds = df.date_seq[id].split()
    date_of_dx = pd.Timestamp(ds[ix[0]])
    year_of_dx = date_of_dx.year
    
    enrollment = {}
    for year in [year_of_dx-2, year_of_dx-1, year_of_dx, year_of_dx+1, year_of_dx+2]:
        if year not in df_dict:
            return False
        else:
            df = df_dict[year]
            if id not in df.index:
                return False
            else:
                enrollment[year] = df.loc[id, 'fully_enrolled'] == 1
    return np.all(enrollment.values())


# Patients were excluded if they had surgery prior to the first diagnosis code, or in the 6 weeks following first diagnosis,
# if they had surgery for cancer, or if they had emergency surgery as defined by an emergency code within 1 week of surgery. 

cancer_surgery_ICD_codes = '153 153.0 153.1 153.2 153.3 153.4 153.5 153.6 153.7 153.8 153.9 154 154.0 154.1 154.2 154.3' \
    + ' 154.8 209.10 209.11 209.12 209.13 209.14 209.15 209.16 209.50 209.51 209.52 209.53 209.54 209.55 209.56 230.3 230.4 556.4'
cancer_surgery_ICD_codes = cancer_surgery_ICD_codes.replace('.', '').split()
cancer_surgery_ICD_codes = set(['icd9-'+x for x in cancer_surgery_ICD_codes])

def surgery_for_cancer(code_seq):
    """test if a code sequence contains a cancer surgery icd code

    Parameters
    ----------
    code_seq : str of icd, cpt, ndc codes

    Results
    -------
    returns bool, True iff cancer surgery icd code appears in code
    sequence

    """
    icd_codes_in_seq = cancer_surgery_ICD_codes & set(code_seq.split())
    return int(len(icd_codes_in_seq) > 0)

surgery_ICD_codes = '045.41 045.7 045.71 045.72 045.73 045.74 045.75 045.76 045.79 045.8 045.82 045.83 045.92 045.93 045.94 046.01 ' \
    + '046.03 046.04 046.1 046.10 046.11 046.13 046.14 0462 04620 04621 04622 04623 04624 046.43 048.62 048.63 017.3 017.31 017.32 017.33 ' \
    + '017.34 017.35 017.36 017.39 045.81'
surgery_ICD_codes = surgery_ICD_codes.replace('.', '').split()

surgery_CPT_codes = '44110 44111 44130 44139 44140 44141 44143 44144 44145 44146 44147 44150 44151 44155 ' \
    + '44156 44157 44158 44160 44320 44187 44188 44204 44205 44206 44207 44208 44210 44211 44212 44213 44227 44238'
surgery_CPT_codes = surgery_CPT_codes.split()

# need to prepend icd9 and cpt to these cause lists
surgery_ICD_codes = ['icd9-'+c for c in surgery_ICD_codes]
surgery_CPT_codes = ['cpt-'+c for c in surgery_CPT_codes]


def emergency_surgery(df, id):
    """test if a patient had emergency surgery as defined by an emergency
    code within 1 week of surgery.


    Parameters
    ----------
    df : pd.DataFrame, with columns code_seq and date_seq
    id : int, patient id

    Results
    -------
    returns bool, True iff continuously enrolled for two years before
    and after year of diagnosis

    """

    t = pd.Series(df.code_seq[id].split())
    ix, = np.where(t.isin(surgery_CPT_codes + surgery_ICD_codes))
    if len(ix) == 0:
        # no surgery => not emergent
        return 0
    # index of first surgery encounter
    i = ix[0]
    
    # date of first surgery
    tt = pd.Series(df.date_seq[id].split()).map(pd.Timestamp)
    t0 = tt[i]
    
    # indices of all encounters from surgery to week after surgery
    t1 = t0 + pd.Timedelta(weeks=1)

    # 1 week before surgery is also within 1 week of surgery
    t0 = t0 - pd.Timedelta(weeks=1)
    
    # limitation of this approach: misses elective surgery that leads to emergent encounter
    ix, = np.where((tt >= t0) & (tt <= t1))
    
    # was any in an emergency setting?
    ttt = pd.Series(df.emrg_seq[id].split()).map(int)
    return int(np.any(ttt[ix]))

def included_subjects(df):
    """identify rows of df that correspond to subjects who meet the
    following inclusion criteria: a new diagnosis of diverticulitis
    and two years of continuous enrollment before and after the year
    of diagnosis; and not surgery for cancer, or emergency surgery as
    defined by an emergency code within 1 week of surgery.

    Parameters
    ----------
    df : pd.DataFrame with columns code_seq, date_seq, emrg_seq

    Results
    -------
    return list of rows

    """
    initially_included_subjects = []
    cancer_exclusion = []
    emergency_exclusion = []
    subjects = []

    for row in df.index:
        if is_included(df, row):
            initially_included_subjects.append(row)

            if surgery_for_cancer(df.code_seq[row]):
                cancer_exclusion.append(row)
            else:
                if emergency_surgery(df, row):
                    emergency_exclusion.append(row)
                else:
                    subjects.append(row)
            
    print('Initially included {} patients'.format(len(initially_included_subjects)))

    print('of which {} were finally included in analysis'.format(len(subjects)))

    return subjects

subjs_wo_dx = []
def seqs_during_exposure_period(df, id, weeks_before, weeks_after):
    """clip sequences to include only specified time period
    
    Parameters
    ----------
    df : pd.DataFrame with columns code_seq, date_seq
    id : row in df to clip
    weeks_before, weeks_after : int specifying time period to clip to
    
    Results
    -------
    returns pd.Series with code_seq, date_seq
    """
    global subjs_wo_dx

    t = pd.Series(df.code_seq[id].split())
    ix, = np.where(t.isin(colonic_dvt_codes)) # ix_,_ is weird because np.where has strange return format
    if len(ix) == 0:
        # no dx, should not be in cohort
        subjs_wo_dx.append(id)
        return pd.Series(
            {'code_seq': '',
             'date_seq': ''})
    
    # index of first diagnosis
    i = ix[0]
    
    # date of first dx
    tt = pd.Series(df.date_seq[id].split()).map(pd.Timestamp)
    t1 = tt[i]
    
    # XXX weeks before dx
    t0 = t1 - pd.Timedelta(weeks=weeks_before)
    
    # YYY weeks after dx
    t1 = t1 + pd.Timedelta(weeks=weeks_after)
    
    ix, = np.where((tt >= t0) & (tt <= t1))

    return pd.Series(
            {'code_seq': ' '.join(t[ix]),
             'date_seq': ' '.join([d.strftime('%Y-%m-%d') for d in tt[ix]])})

def days_until_surgery(s):
    """calculate time from diagnosis until surgery in days

    Parameters
    ----------
    s : pd.Series

    Results
    -------

    Returns days as float, or np.inf if no surgery took place

    """
    cs = s['code_seq'].split()
    cs = pd.Series(cs)
    surgery_ix, = np.where(cs.isin(surgery_CPT_codes + surgery_ICD_codes))

    if len(surgery_ix) > 0:
        cs = pd.Series(cs)
        ds = pd.Series(s['date_seq'].split())
        ds = ds.map(pd.Timestamp)
        
        surgery_0 = surgery_ix[0]
        day_of_surgery = ds[surgery_0]
        
        dx_ix, = np.where(cs.isin(colonic_dvt_codes))
        if len(dx_ix) == 0:
            # no dx, should not be in cohort
            return np.nan
        
        # index of first diagnosis
        dx_0 = dx_ix[0]
        # date of first dx
        t0 = ds[dx_0]
        return (day_of_surgery - t0).days
    else:
        return np.inf

def clipped_labeled_sequences(df, subjects, weeks_before, weeks_after):
    """transform full dataframe by selecting only subject rows, and only
    sequence from weeks_before to weeks_after; then label with days until surgery

    Parameters
    ----------
    df : pd.DataFrame with columns code_seq, date_seq
    subjects : rows in df to keep
    weeks_before, weeks_after : int specifying time period to clip to
    
    Results
    -------
    returns pd.DataFrame with code_seq (str), date_seq (str), and y_days (float)
    """
    patient_df = []
    for subj_id in subjects:
        s = seqs_during_exposure_period(df, subj_id, weeks_before, weeks_after)
        s['y_days'] = days_until_surgery(df.loc[subj_id])
        patient_df.append(s)
    
    patient_df = pd.DataFrame(patient_df, index=subjects)
    return patient_df

def bigram_feature_vectors(df):
    """form bigram features from code sequence in df

    Parameters
    ----------
    df : pd.DataFrame with code_seq column
    
    Results
    -------
    returns sparse array of bigram counts
    """

    import sklearn.feature_extraction

    ngram_range = (1,2)

    trx = sklearn.feature_extraction.text.CountVectorizer(
        ngram_range=ngram_range,
        min_df=10,  # minimum number of docs that must contain n-gram to include as a column
        tokenizer=lambda x: [x_i.strip() for x_i in x.split()]  # keep '-' characters in tokens
    )
    
    X = trx.fit_transform(df.code_seq.fillna(''))
    return X

def load_prepped_df(weeks_after=48):
    """Load prepped dataframe for code sequences up to specified number of
    weeks after diagnosis; after filtering to remove surgeries before
    52 weeks.

    Parameters
    ----------
    weeks_after : int, cached for values in range(-4, 49, 4)

    Results
    -------
    returns df, X, y
    """

    dname = '/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/prepped_data/'
    fname = dname + 'clipped_{:02d}_labeled_subject_sequences.csv'.format(weeks_after)

    patient_df = pd.read_csv(fname, index_col=0)

    patient_df = patient_df[patient_df.y_days >= 52]
    X = bigram_feature_vectors(patient_df)
    y = np.array(patient_df.y_days <= 2*52*7, dtype=float)

    return patient_df, X, y
