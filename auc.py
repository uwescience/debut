import sys, pandas as pd
import sklearn.naive_bayes, sklearn.ensemble, sklearn.linear_model, sklearn.model_selection
import data, model

assert len(sys.argv) in [2,], 'usage: python auc.py rep'
rep = int(sys.argv[1])
print(sys.argv)

weeks_after = 48 # TODO: make this a parameter

patient_df, X, y = data.load_prepped_df(weeks_after)

# use a subset of data for faster testing
#patient_df = patient_df.iloc[:2000]
#X = X[:2000]
#y = y[:2000]

n_jobs = 10
clf_dict = {'GBM': sklearn.model_selection.GridSearchCV(sklearn.ensemble.GradientBoostingClassifier(),
                                                        param_grid={'max_depth':[1,3,5,7,9,11]}, n_jobs=n_jobs),
            'NB': sklearn.model_selection.GridSearchCV(sklearn.naive_bayes.BernoulliNB(),
                                                       param_grid={'alpha':[0, .01, .1, 1., 10., 100.]}, n_jobs=n_jobs),
            'PLR': sklearn.linear_model.LogisticRegressionCV(n_jobs=n_jobs, class_weight='balanced'),
            'RF': sklearn.ensemble.RandomForestClassifier(n_estimators=100, n_jobs=n_jobs, class_weight='balanced'),
           }

all_results = pd.DataFrame()
for clf_name, clf in clf_dict.iteritems():
    print(clf_name)
    sys.stdout.flush()

    results = model.auc_est(clf, X, y, [rep], range(10))
    results['clf_name'] = clf_name
    results['weeks_after'] = weeks_after
    print(results.auc.describe())
    all_results.append(results)

    dname = '/homes/abie/projects/2016/TICS/'
    all_results.to_csv(dname + 'auc_results_{:02d}_{:02d}.csv'.format(rep, weeks_after), index=False)

