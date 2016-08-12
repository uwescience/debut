# -*- coding: utf-8 -*-
# <nbformat>3.0</nbformat>

# <codecell>

!date
import numpy as np, pandas as pd, matplotlib.pyplot as plt, seaborn as sns
%matplotlib inline
sns.set_context('paper')
sns.set_style('darkgrid')
pd.set_option('max_rows',10)

import time

# <codecell>

import sklearn.naive_bayes, sklearn.model_selection

# <codecell>

import glob

# <codecell>

dname='/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/prepped_data/'

# <codecell>

%%time

# fast for testing
#nrows = 10000
# full data
nrows = None

df_dict = {}
for fname in sorted(glob.glob(dname + '20*.csv')):
    t = pd.read_csv(fname, nrows=nrows, index_col='id')
    y = t.year.iloc[0]
    assert np.all(t.year == y)
    df_dict[y] = t

# <codecell>

%%time

# merge code sequence and every surgery for all years for these patients
t = df_dict[2007]

code_seq = t.code_seq.fillna('')
date_seq = t.date_seq.fillna('')
emrg_seq = t.emrg_seq.fillna('')
in_seq = t.in_seq.fillna('')

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
    
code_seq = code_seq.fillna('')
date_seq = date_seq.fillna('')
emrg_seq = emrg_seq.fillna('')
in_seq = in_seq.fillna('')

# <codecell>

t.head()

# <codecell>

colonic_dvt_codes = '56211 56213'.split()

# need to prepend icd9 to the cause list
colonic_dvt_codes = ['icd9-'+c for c in colonic_dvt_codes]

# <codecell>

# Using the MarketScan Commercial Claims database (Truven Health Analytics),
# we selected all adult patients with a new diagnosis of diverticulitis
# and two years of continuous enrollment before and after the year of diagnosis

def is_included(id):
    cs = pd.Series(code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) == 0:
        return False  # no dx, should not be in cohort
    
    ds = date_seq[id].split()
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

is_included(74901)
# TODO: test carefully

# <codecell>

%%time

initially_included_subjects = pd.Series(code_seq.index, index=code_seq.index).map(is_included)

# <codecell>

initially_included_subjects = initially_included_subjects[initially_included_subjects].index
len(initially_included_subjects)

# <codecell>

# Patients were excluded if they had surgery prior to the first diagnosis code, or in the 6 weeks following first diagnosis,
# if they had surgery for cancer, or if they had emergency surgery as defined by an emergency code within 1 week of surgery. 

cancer_surgery_ICD_codes = '153 153.0 153.1 153.2 153.3 153.4 153.5 153.6 153.7 153.8 153.9 154 154.0 154.1 154.2 154.3' \
    + ' 154.8 209.10 209.11 209.12 209.13 209.14 209.15 209.16 209.50 209.51 209.52 209.53 209.54 209.55 209.56 230.3 230.4 556.4'
cancer_surgery_ICD_codes = cancer_surgery_ICD_codes.replace('.', '').split()
cancer_surgery_ICD_codes = set(['icd9-'+x for x in cancer_surgery_ICD_codes])

def surgery_for_cancer(code_seq):
    icd_codes_in_seq = cancer_surgery_ICD_codes & set(code_seq.split())
    return int(len(icd_codes_in_seq) > 0)
surgery_for_cancer(code_seq[28201])
# TODO: test more

# <codecell>

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

# <codecell>

'icd9-04610' in surgery_ICD_codes

# <codecell>

# if they had emergency surgery as defined by an emergency code
# within 1 week of surgery. 

def emergency_surgery(id):
    """ use code_seq, data_seq, and emrg_seq"""
    t = pd.Series(code_seq[id].split())
    ix, = np.where(t.isin(surgery_CPT_codes + surgery_ICD_codes))
    if len(ix) == 0:
        # no surgery => not emergent
        return 0
    # index of first surgery encounter
    i = ix[0]
    
    # date of first surgery
    tt = pd.Series(date_seq[id].split()).map(pd.Timestamp)
    t0 = tt[i]
    
    # indices of all encounters from surgery to week after surgery
    t1 = t0 + pd.Timedelta(weeks=1)

    # 1 week before surgery is also within 1 week of surgery
    t0 = t0 - pd.Timedelta(weeks=1)
    
    # limitation of this approach: misses elective surgery that leads to emergent encounter
    ix, = np.where((tt >= t0) & (tt < t1))
    
    # was any in an emergency setting?
    ttt = pd.Series(emrg_seq[id].split()).map(int)
    return int(np.any(ttt[ix]))

emergency_surgery(212002)
# TODO: test more

# <codecell>

def additional_exclusions(id):
    if surgery_for_cancer(code_seq[id]):
        return True
    if emergency_surgery(id):
        return True
    return False
additional_exclusions(28201)
additional_exclusions(212002)
#np.where(np.array(map(additional_exclusions, no_dvt_during_washout))==0)
# TODO: test carefully

# <codecell>

len(initially_included_subjects)

# <codecell>

%time subjects = [id for id in list(initially_included_subjects) if not additional_exclusions(id)]

# <codecell>

len(subjects)

# <codecell>

# In order to ensure equal exposure, we collected claims data for the XXX weeks before the diagnosis to YYY weeks after diagnosis

weeks_before = 52
weeks_after = 104

subjs_wo_dx = []

def seqs_during_exposure_period(id):
    """ use code_seq, data_seq, and emrg_seq"""
    t = pd.Series(code_seq[id].split())
    ix, = np.where(t.isin(colonic_dvt_codes)) # ix_,_ is weird because np.where has strange return format
    if len(ix) == 0:
        # no dx, should not be in cohort
        subjs_wo_dx.append(id)
        return pd.Series(
            {'code_seq': np.nan,
             'date_seq': np.nan})
    
    # index of first diagnosis
    i = ix[0]
    
    # date of first dx
    tt = pd.Series(date_seq[id].split()).map(pd.Timestamp)
    t1 = tt[i]
    
    # XXX weeks before dx
    t0 = t1 - pd.Timedelta(weeks=weeks_before)
    
    # YYY weeks after dx
    t1 = t1 + pd.Timedelta(weeks=weeks_after)
    
    ix, = np.where((tt >= t0) & (tt < t1))

    return pd.Series(
            {'code_seq': ' '.join(t[ix]),
             'date_seq': ' '.join([d.strftime('%Y-%m-%d') for d in tt[ix]])})

seqs_during_exposure_period(8980502)
# TODO: test more

# <codecell>

%time patient_df = pd.DataFrame(map(seqs_during_exposure_period, subjects), index=subjects)

# <codecell>

# As outcome, we found the time until surgery for those patients who went on to have surgery

def days_until_surgery(s):
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


# test apply
pd.DataFrame(dict(code_seq=code_seq, date_seq=date_seq, emrg_seq=emrg_seq))\
    .fillna('').iloc[:10].apply(days_until_surgery, axis=1)
# TODO: check if results are correct

# test single
days_until_surgery({'code_seq': code_seq.iloc[10],
                   'date_seq': date_seq.iloc[10],
                  })

# <codecell>

%%time

y_days = pd.DataFrame(dict(code_seq=code_seq, date_seq=date_seq, emrg_seq=emrg_seq))\
    .fillna('').loc[patient_df.index].apply(days_until_surgery, axis=1)

# <codecell>

def age_at_dx(id):
    cs = pd.Series(code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) == 0:
        return np.nan  # no dx, should not be in cohort
    
    ds = date_seq[id].split()
    date_of_dx = pd.Timestamp(ds[ix[0]])
    year_of_dx = date_of_dx.year
    
    return df_dict[year_of_dx].loc[id, 'age']

age_at_dx(74901)
# TODO: test carefully

# <codecell>

patient_ages = []
for id in subjects:
    patient_ages.append(age_at_dx(id))

# <codecell>

np.mean(patient_ages), np.std(patient_ages)

# <codecell>

def sex_at_dx(id):
    cs = pd.Series(code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) == 0:
        return np.nan  # no dx, should not be in cohort
    
    ds = date_seq[id].split()
    date_of_dx = pd.Timestamp(ds[ix[0]])
    year_of_dx = date_of_dx.year
    
    return df_dict[year_of_dx].loc[id, 'sex']

sex_at_dx(74901)
# TODO: test carefully

# <codecell>

%%time

patient_sex = []
for id in subjects:
    patient_sex.append(sex_at_dx(id))

# <codecell>

patient_sex = np.array(patient_sex)
100*np.mean(patient_sex == 2)  # pct female

# <codecell>

np.mean(y_days.loc[subjects] < 2*52*7)*100

# <codecell>

def at_most_two_episodes(id):
    cs = pd.Series(code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) <= 2:
        return True
    
    ds = date_seq[id].split()
    dates_of_dx = [pd.Timestamp(ds[i]) for i in ix]
    
    distinct_episodes = 1
    last_episode_start = dates_of_dx[0]
    for d in dates_of_dx:
        if (d - last_episode_start) > pd.Timedelta(weeks=6):
            last_episode_start = d
            distinct_episodes += 1
    return distinct_episodes <= 2

at_most_two_episodes(74901)
# TODO: test carefully

# <codecell>

rows = (y_days.loc[subjects] >= 52*7) & (y_days.loc[subjects] < 2*52*7)

# <codecell>

ix = list(y_days[rows].index)

# <codecell>

%%time

early_surgery = []
for id in ix:
    early_surgery.append(at_most_two_episodes(id))

# <codecell>

len(early_surgery)

# <codecell>

np.mean(early_surgery)*100

# <markdowncell>

# Investigate this early surgery stuff...

# <codecell>

rows = (y_days.loc[subjects] >= 12*7) & (y_days.loc[subjects] < 52*7)

# <codecell>

ix = list(y_days[rows].index)

# <codecell>

%%time

early_surgery = []
for id in ix:
    early_surgery.append(at_most_two_episodes(id))

# <codecell>

len(early_surgery), np.mean(early_surgery)*100

# <markdowncell>

# Val had a more complicated definition of early surgery, here is an approximation of it:

# <codecell>

def at_most_two_inpatient_episodes(id):
    cs = pd.Series(code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) <= 2:
        return True
    
    ds = pd.Series(date_seq[id].split())
    dates_of_dx = ds.map(pd.Timestamp)
    
    ins = in_seq[id].split()
    
    distinct_episodes = 1
    last_episode_start = dates_of_dx[ix[0]]
    for i in ix:
        d = dates_of_dx[i]
        if (d - last_episode_start) > pd.Timedelta(weeks=6):
            if int(ins[i]) == 1:
                # this was an inpatient episode, count it
                last_episode_start = d
                distinct_episodes += 1
                       
    return distinct_episodes <= 2

at_most_two_inpatient_episodes(278802)
# TODO: test carefully

# <codecell>

rows = (y_days.loc[subjects] >= 52*7) & (y_days.loc[subjects] < 2*52*7)
ix = list(y_days[rows].index)
early_surgery = []
for id in ix:
    early_surgery.append(at_most_two_inpatient_episodes(id))
len(early_surgery), np.mean(early_surgery)*100

# <markdowncell>

# Lucas requested an intermediate version (which was originally complex, but then he simplified):
# 
#     I was thinking about simplifying my request from last week (below). For those patients who undergo surgery, I would like to know what percent have fewer than 3 prior to resection, i.e. inpatient diagnosis OR outpatient diagnosis plus one code for each of the outpatient antibiotics (ciprofloxacin and metronidazole) [attached file] within 7 days of the diagnosis code.
#     
#     
#     Inpatient Antibiotic codes:
# 
#     J0743, J1335, J2185, J0692, J0698, J0712, J0715, J0696, G9313, J0295, S0040, J2543, S0077, S0030, J0744, J1956, J2280, C9282, G9314, G9315

# <codecell>

l1 = pd.read_excel('/homes/abie/projects/2016/TICS/antibiotics.xlsx',
                   header=None,
                   names=['ndc'],
                   sheetname='Ciprofloxacin')
l2= pd.read_excel('/homes/abie/projects/2016/TICS/antibiotics.xlsx',
                   header=None,
                   names=['ndc'],
                   sheetname='Metronidazole')
s1 = set(['ndc-'+str(x) for x in l1.ndc])
s2 = set(['ndc-'+str(x) for x in l2.ndc])

# <codecell>

def at_most_two_episodes_better(id):
    cs = pd.Series(code_seq[id].split())
    ix, = np.where(cs.isin(colonic_dvt_codes)) # trailing comma in "ix," is weird, used because np.where has strange return format
    if len(ix) <= 2:
        return True
    
    ds = pd.Series(date_seq[id].split())
    dates_of_dx = ds.map(pd.Timestamp)
    
    ins = in_seq[id].split()
    
    distinct_episodes = 1
    last_episode_start = dates_of_dx[ix[0]]
    for i in ix:
        d = dates_of_dx[i]
        if (d - last_episode_start) > pd.Timedelta(weeks=6):
            if int(ins[i]) == 1:
                # this was an inpatient episode, count it
                last_episode_start = d
                distinct_episodes += 1
            else:
                # check if two drug combo appears in next week
                next_weeks_ix = np.where((dates_of_dx >= d) & (dates_of_dx <= d + pd.Timedelta(days=7)))
                next_weeks_codes = set(cs.iloc[next_weeks_ix])
                
                if len(next_weeks_codes & s1) > 0:
                    if len(next_weeks_codes & s2) > 0:
                        # both drugs coded in week after encounter, consider it an episode
                        #print next_weeks_codes
                        last_episode_start = d
                        distinct_episodes += 1
                       
    return distinct_episodes <= 2

at_most_two_episodes_better(278802)
# TODO: test carefully

# <codecell>

rows = (y_days.loc[subjects] >= 52*7) & (y_days.loc[subjects] < 2*52*7)
ix = list(y_days[rows].index)
early_surgery = []
for id in ix:
    early_surgery.append(at_most_two_episodes_better(id))
len(early_surgery), np.mean(early_surgery)*100

