import sys, numpy as np, pandas as pd
import sklearn.naive_bayes, sklearn.ensemble, sklearn.linear_model, sklearn.model_selection
import data, model

assert len(sys.argv) == 5, 'usage: python auc.py rep weeks ngram_min ngram_max'
rep = int(sys.argv[1])
weeks_after = int(sys.argv[2])
ngram_min = int(sys.argv[3])
ngram_max = int(sys.argv[4])
print(sys.argv)

# set random seed for reproducibility
np.random.seed(12345+rep)

# load data
patient_df, X, y = data.load_prepped_df(weeks_after, ngram_range=(ngram_min, ngram_max))

# create dict of ML methods to consider
n_jobs = 10  # make sure to request corresponding resource level on cluster
clf_dict = {'GBM': sklearn.model_selection.GridSearchCV(sklearn.ensemble.GradientBoostingClassifier(),
                                                        param_grid={'max_depth':[1,3,5,7,9,11]}, n_jobs=n_jobs),
            'NB': sklearn.model_selection.GridSearchCV(sklearn.naive_bayes.BernoulliNB(),
                                                       param_grid={'alpha':[0, .01, .1, 1., 10., 100.]}, n_jobs=n_jobs),
            'PLR': sklearn.linear_model.LogisticRegressionCV(n_jobs=n_jobs, class_weight='balanced'),
            'RF': sklearn.ensemble.RandomForestClassifier(n_estimators=100, n_jobs=n_jobs, class_weight='balanced'),
           }

# run models and save results
all_results = pd.DataFrame()
for clf_name, clf in clf_dict.items():
    print(clf_name)
    sys.stdout.flush()

    results = model.auc_est(clf, X, y, [rep], range(10))
    results['clf_name'] = clf_name
    results['weeks_after'] = weeks_after
    print(results.auc.describe())
    all_results = all_results.append(results)

    # save results as you go, to fail faster
    dname = '/homes/abie/projects/2016/TICS/'
    all_results.to_csv(dname + 'auc_results_{:02d}_{:02d}_{:d}-{:d}.csv'.format(rep, weeks_after, ngram_min, ngram_max), index=False)

