"""
This script projects the CCA embeddigns to 2d using t-SNE
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA
import sklearn.manifold

path = '/ihme/scratch/users/cjones6/temp_data/'
# Read in embeddings
embeddings = np.genfromtxt(path + 'saved_eigenvectors_regularized25.txt')
# Only keep the first 10k because the results using more didn't turn out well
# (Seemed to converge to bad local minimum)
embeddings = embeddings[0:10000, :]
# Project the embeddings to 2d
embed = sklearn.manifold.TSNE(learning_rate=1000, random_state=1, verbose=1, n_iter_without_progress=100, perplexity=50.0)
embeddings = embed.fit_transform(embeddings)
# Save results
np.savetxt(path + 'embed2d_results.txt', embeddings)
print 'Done!'
