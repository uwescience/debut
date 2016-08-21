import sys
import pandas as pd

assert len(sys.argv) in [2,3], 'usage: python etl.py YEAR [fast_test]'
print sys.argv[1:]

year = int(sys.argv[1])
if len(sys.argv) == 3:
    assert sys.argv[2] == 'fast_test'
    fast_test = True
else:
    fast_test = False

# for testing, load only part of dataframe
def partial_data_frame(self, lines):
    """
    to_data_frame() -> pandas.DataFrame object

    A convenience method to convert a SAS7BDAT file into a pandas
    DataFrame.
    """
    import pandas as pd
    data = []
    for i, l_i in enumerate(self.readlines()):
        data.append(l_i)
        if i == lines-1:
            break
    return pd.DataFrame(data[1:], columns=data[0], dtype='str')

# load data (slow)
dname = '/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/raw_data/'
def read_sas(fname):
    import sas7bdat
    with sas7bdat.SAS7BDAT(fname) as f:
        if fast_test:
            df = partial_data_frame(f, 1000)
        else:
            df = f.to_data_frame()
        df.header = f.header
    return df

def load(year):
    import sys
    tics = {}

    for letter in 'adios':
        print letter,
        sys.stdout.flush
        fname = dname + 'tics_cohort{}_{:02d}.sas7bdat'.format(letter, year-2000)
        tics[letter, year] = read_sas(fname)
    print

    return tics
tics = load(year)



y = year
# group all cohort files by id for easy access
id_list = tics['a',y].ENROLID.unique()

_gtics = {}
for l in 'aodis':
    _gtics[l,y] = tics[l,y].groupby('ENROLID')

colonic_dvt_codes = '56211 56213'.split()

def has_dvt_dx(s):
    for var in ['DX1', 'DX2', 'DX3', 'DX4']:
        if str(s[var]) in colonic_dvt_codes:
            return True
    return False
assert has_dvt_dx(pd.Series({'DX1': '', 'DX2': '', 'DX3': '', 'DX4': '',})) == False
assert has_dvt_dx(pd.Series({'DX1': '56211', 'DX2': '', 'DX3': '', 'DX4': '',})) == True
assert has_dvt_dx(pd.Series({'DX1': 'N10', 'DX2': '56213', 'DX3': '', 'DX4': '',})) == True
assert has_dvt_dx(pd.Series({'DX1': '', 'DX2': '', 'DX3': '56213', 'DX4': '',})) == True
assert has_dvt_dx(pd.Series({'DX1': '', 'DX2': '', 'DX3': '', 'DX4': '56213',})) == True


surgery_ICD_codes = '45.41 45.7 45.71 45.72 45.73 45.74 45.75 45.76 45.79 45.8 45.82 45.83 45.92 45.93 45.94 46.01 ' \
    + '46.03 46.04 46.1 46.10 46.11 46.13 46.14 462 4620 4621 4622 4623 4624 46.43 48.62 48.63 17.3 17.31 17.32 17.33 ' \
    + '17.34 17.35 17.36 17.39 45.81'
surgery_ICD_codes = surgery_ICD_codes.replace('.', '').split()

surgery_CPT_codes = '44110 44111 44130 44139 44140 44141 44143 44144 44145 44146 44147 44150 44151 44155 ' \
    + '44156 44157 44158 44160 44320 44187 44188 44204 44205 44206 44207 44208 44210 44211 44212 44213 44227 44238'
surgery_CPT_codes = surgery_CPT_codes.split()

def has_surgery_code(s):
    if str(s['PROC1']) in surgery_CPT_codes:
        return True

    if str(s['DX1']) in surgery_ICD_codes:
        return True
    if str(s['DX2']) in surgery_ICD_codes:
        return True
    if str(s['DX4']) in surgery_ICD_codes:
        return True
    if str(s['DX3']) in surgery_ICD_codes:
        return True
    return False

# assert has_surgery_code(pd.Series({'PROC1': '', 'DX1': 0, 'DX2':0})) == False
# assert has_surgery_code(pd.Series({'PROC1': '', 'DX1': 0, 'DX2':'4541'})) == True
# assert has_surgery_code(pd.Series({'PROC1': '44238', 'DX1': 0, 'DX2':0})) == True
# assert has_surgery_code(pd.Series({'PROC1': '', 'DX1': 4541, 'DX2':0})) == True



emergent_CPT_codes = '99281 99282 99283 99284 99285 G0380 G0381 G0382 G0383 G0384'.split()
def has_emergent_code(s):
    if str(s['PROC1']) in emergent_CPT_codes:
        return True

    # question: do emergency codes ever appear in dx columns?
    #     if str(s['DX1']) in emergent_CPT_codes:
    #         return True
    #     if str(s['DX2']) in emergent_CPT_codes:
    #         return True

    if str(s['STDPLAC']) in ['20', '23']:  # 20 = Urgent Care, 23 = Emergency Room - Hospital 
        return True
    
    if str(s['STDPROV']) in ['220']:  # 220 = Emergency Medicine 
        return True
    return False


assert has_emergent_code(pd.Series({'PROC1': '', 'STDPLAC':0, 'STDPROV':0})) == False
assert has_emergent_code(pd.Series({'PROC1': '99281'})) == True
assert has_emergent_code(pd.Series({'PROC1': 99281})) == True
assert has_emergent_code(pd.Series({'PROC1': '', 'STDPLAC':20})) == True
assert has_emergent_code(pd.Series({'PROC1': '', 'STDPLAC':'', 'STDPROV':220})) == True



def feature_for(key):
    t = {}
    for l in 'aodis':
        try:
            t[l,y] = _gtics[l,y].get_group(key)
        except KeyError:
            t[l,y] = pd.DataFrame()


    # merge relevant tables for this individual
    df = pd.DataFrame(columns=['SVCDATE', 'NDCNUM', 'DX1', 'DX2', 'DX3', 'DX4', 'PROC1', 'STDPLAC', 'STDPROV', 'table'])  # include columns that are required
    for l in 'ods':
        tt = t[l,y].copy()
        tt['table'] = l
        df = df.append(tt, ignore_index=True)
    df = df.sort_values('SVCDATE')

    # data from annual enrollment table
    if len(t['a',y]) == 0:
        return None
    tt = t['a',y].iloc[0]

    age = tt['AGE']
    sex = int(tt['SEX'])
    year = tt['YEAR']
    geo = int(tt['EGEOLOC'])
    relation = int(tt['EMPREL'])
    fully_enrolled = tt['ENRMON'] == 12

    dvt = 0
    emergency_dvt = 0
    dvt_surgery = 0

    # extract sequence data
    code_seq, date_seq, emrg_seq = [], [], []
    out_seq, in_seq = [], []
    pay_seq, copay_seq, deduct_seq, coins_seq, cob_seq = [], [], [], [], []
    for i, tt in df.iterrows():
        dt = tt['SVCDATE']
        if has_dvt_dx(tt) or has_surgery_code(tt):
            dvt = 1
            if has_emergent_code(tt):
                emergency_dvt = 1
                    
            if has_surgery_code(tt):
                dvt_surgery = 1

        
        for col in ['DX1', 'DX2', 'DX3', 'DX4', 'PROC1', 'NDCNUM']:
            dx = tt[col]
            if str(dx).strip() not in ['', 'nan']:
                # include prefix icd-, cpt-, and ndc- for figuring out what is what later
                if col.startswith('DX'):
                    dx = 'icd9-' + dx
                elif col == 'PROC1':
                    dx = 'cpt-' + dx
                elif col == 'NDCNUM':
                    dx = 'ndc-' + dx

                code_seq.append(dx)
                date_seq.append(tt['SVCDATE'])
                emrg_seq.append(str(int(has_emergent_code(tt))))
                out_seq.append(str(int(tt['table'] == 'o')))
                in_seq.append(str(int(tt['table'] == 's')))
                pay_seq.append(str(tt['PAY']))
                copay_seq.append(str(tt['COPAY']))
                deduct_seq.append(str(tt['DEDUCT']))
                coins_seq.append(str(tt['COINS']))
                cob_seq.append(str(tt['COB']))

    code_seq = ' '.join(code_seq)
    date_seq = ' '.join([d.strftime('%Y-%m-%d') for d in date_seq])
    emrg_seq = ' '.join(emrg_seq)
    in_seq = ' '.join(in_seq)
    out_seq = ' '.join(out_seq)

    pay_seq = ' '.join(pay_seq)
    copay_seq = ' '.join(copay_seq)
    deduct_seq = ' '.join(deduct_seq)
    coins_seq = ' '.join(coins_seq)
    cob_seq = ' '.join(cob_seq)

    return dict(id=int(key), age=int(age), sex=sex, year=int(year),
                fully_enrolled=int(fully_enrolled),
                dvt=dvt, emergency_dvt=emergency_dvt,
                dvt_surgery=dvt_surgery,
                code_seq=code_seq, date_seq=date_seq,
                emrg_seq=emrg_seq, out_seq=out_seq, in_seq=in_seq,
                pay_seq=pay_seq, copay_seq=copay_seq, deduct_seq=deduct_seq, coins_seq=coins_seq, cob_seq=cob_seq, 
    )

# group all cohort files by id for easy access
X_i = feature_for(id_list[0])

id_list = tics['a',y].ENROLID.unique()
X = []
for id in id_list:
    X.append(feature_for(id))
    # TODO: include some feedback about progress, and consider making
    # incremental saves to that it is possible to see partial results
    # while process is running

df = pd.DataFrame(X, columns=['id', 'year', 'age', 'sex',
                              'dvt', 'emergency_dvt', 'dvt_surgery',
                              'fully_enrolled',
                              'code_seq', 'date_seq', 'emrg_seq',
                              'out_seq', 'in_seq',
                              'pay_seq', 'copay_seq', 'deduct_seq', 'coins_seq', 'cob_seq',
                          ])
dname = '/home/j/LIMITED_USE/PROJECT_FOLDERS/DEBUT/prepped_data/'
fname = dname + '{}.csv'.format(year)
if fast_test:
    fname += '_fast'
df.to_csv(fname, index=False)

