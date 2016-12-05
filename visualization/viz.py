"""
This script takes results from using t-SNE on the CCA embeddings and then plots the new points.
It also zooms in on a specific area and labels the points in that area.
"""

import json
import matplotlib
# The following line is here because I got an error without it
# http://stackoverflow.com/questions/38612473/pyplot-cannot-connect-to-x-server-localhost10-0-despite-ioff-and-matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np


# Location of previous results
folder = '/ihme/scratch/users/cjones6/temp_data/'

# Read in results from t-SNE
embeddings = np.genfromtxt(folder+'embed2d_results.txt')

# Read in dictionaries that convert indices to codes and vice versa
code_to_int, int_to_code, code_counts, unique_code_counts, n_codes = json.load(open(folder+'saved_dicts', 'r'))

# Labels for points
labels = [int_to_code[i] for i in range(0, len(int_to_code))]

x = embeddings[:, 0]
y = embeddings[:, 1]


## Plot 1: All of the points
fig, ax = plt.subplots()
plt.scatter(x, y, facecolors='none', edgecolors='black')
plt.xlim([-10, 10])
plt.ylim([-10, 10])
# Display the location of the patch I'm plotting next as a red rectangle
ax.add_patch(
    patches.Rectangle(
        (2.8, -0.7),
        0.4,
        0.3,
        fill=False,
        color='red'
    )
)
# Increase the size of the figure so it doesn't become blurred on the poster
fig.set_size_inches(10, 10)
# Annotate (some of) the points- all is too many!
# for i in range(0, 100)):
#     txt = labels[i]
#     ax.annotate(txt, (x[i], y[i] - 0.01))
# plt.show()
plt.axis('off')
fig.savefig('embeddings_all.png', dpi=100)


# Zoom in on a certain area and plot the points in that area
# Code you want to zoom in on
center_code = 'icd9-56211'
# Get location of that code
idx = code_to_int[center_code]
x_center = x[idx]
y_center = y[idx]

# Check that the nearest neighbors are reasonable. If there not, there's not much point in using either plot. If the
# CCA embeddings are good, the t-SNE optimization probably reached a bad local min.
num_nearby = 5
embedding = embeddings[idx, :]
# Find the distances to the embeddings
dists = [np.linalg.norm(embedding - embeddings[i, :]) for i in range(0, np.size(embeddings, 0))]
nearest_points = np.argsort(dists)[1:num_nearby + 1]
# Print nearest neighbors
for i in range(0, num_nearby):
    print int_to_code[nearest_points[i]], dists[nearest_points[i]]

# Axes areas
halfwidth = .3
# xlims = [x_center-halfwidth, x_center+halfwidth]
# ylims = [y_center-halfwidth, y_center+halfwidth]
xlims = [2.8, 3.2]
ylims = [-0.7, -0.4]

# Plot all points
fig, ax = plt.subplots()
ax.scatter(x, y)

# Label points in that area (had to look up what each code was by hand)
code_to_txt = {'icd9-56211': 'Diverticulitis', 'cpt-99285': 'ED visit', 'cpt-72193': 'CT pelvis',
               'cpt-74160': 'CT abdomen', 'icd9-78900': 'Abdominal pain', 'icd9-78904': 'Abdominal pain lower left quadrant',
               'cpt-74177': 'CT abdomen and pelvis'}
for i in range(0, len(x)):
    if xlims[0] < x[i] < xlims[1] and ylims[0] < y[i] < ylims[1]:
        try:
            txt = code_to_txt[labels[i]]
        except:
            txt = labels[i]
        if labels[i] == 'cpt-72193':
            ax.annotate(txt, (x[i],y[i]-0.01), size='20')
        elif labels[i] == 'cpt-74160':
            ax.annotate(txt, (x[i]-0.09, y[i] - 0.01), size='20')
        else:
            ax.annotate(txt, (x[i], y[i]+0.003), size='20')

plt.xlim(xlims)
plt.ylim(ylims)
plt.axis('off')
fig.set_size_inches(10, 10)
fig.savefig('embeddings.png', dpi=100)



