""" Methods for fitting and predicting in DEBUT analysis

Included methods:
"""

import sys
import numpy as np, pandas as pd
import sklearn.model_selection

def auc_est(clf, X, y, reps, folds):
    """Estimate the area under the receiver-operator-characteristic curve
    (AUC) by repeated 10-fold cross-validation

    Parameters
    ----------
    clf : sklearn.classifier
    X : sparse np.array of feature vectors
    y : np.array of labels
    reps : list of ints, repetitions of 10-fold CV to use
    folds : list of ints, folds to use
    
    Results
    -------
    Returns pd.DataFrame with prediction quality and compute time
    info, as well as rep and fold columns
    """
    results = []
    for rep in range(10):
        cv = sklearn.model_selection.KFold(n_splits=10, shuffle=True, random_state=12345+rep)
        for fold, (train, test) in enumerate(cv.split(X, y)):
            if (rep in reps) and (fold in folds):
                print('rep {}, fold {}'.format(rep, fold))
                sys.stdout.flush()
                # fit on training data
                clf.fit(X[train], y[train])

                # predict on testing data
                ypred_pr = clf.predict_proba(X[test])

                # measure quality of prediction
                auc = sklearn.metrics.roc_auc_score(y[test], ypred_pr[:,-1])
                results.append({
                    'rep': rep,
                    'fold': fold,
                    'clf': str(clf),
                    'auc': auc,
                })
    return pd.DataFrame(results, columns=['rep', 'fold', 'clf', 'auc'])

