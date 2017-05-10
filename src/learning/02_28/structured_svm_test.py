import itertools
import pickle
import numpy as np
from scipy import sparse

from sklearn.metrics import hamming_loss
from sklearn.datasets import fetch_mldata
from sklearn.metrics import mutual_info_score
from scipy.sparse.csgraph import minimum_spanning_tree

from pystruct.learners import OneSlackSSVM
from pystruct.models import MultiLabelClf
from pystruct.datasets import load_scene


def chow_liu_tree(y_):
    # compute mutual information using sklearn
    n_labels = y_.shape[1]
    mi = np.zeros((n_labels, n_labels))
    for i in range(n_labels):
        for j in range(n_labels):
            mi[i, j] = mutual_info_score(y_[:, i], y_[:, j])
    mst = minimum_spanning_tree(sparse.csr_matrix(-mi))
    edges = np.vstack(mst.nonzero()).T
    edges.sort(axis=1)
    return edges


data, labels = pickle.load(open('../../../darkweb_data/2_28/forums40_phrases_train_test.pickle', 'rb'))
train_length = int(0.9 * len(data))
test_length = len(data) - train_length

X_train, X_test = np.array(data[:train_length]), np.array(data[train_length:])
y_train, y_test = np.array(labels[:train_length]), np.array(labels[train_length:])

print(y_train[0])

# scene = load_scene()
# X_train, X_test = scene['X_train'], scene['X_test']
# y_train, y_test = scene['y_train'], scene['y_test']

# print(y_train[0])
n_labels = y_train.shape[1]

full = np.vstack([x for x in itertools.combinations(range(n_labels), 2)])
tree = chow_liu_tree(y_train)

full_model = MultiLabelClf(edges=full, inference_method='qpbo')
independent_model = MultiLabelClf(inference_method='unary')
tree_model = MultiLabelClf(edges=tree, inference_method="max-product")

full_ssvm = OneSlackSSVM(full_model, inference_cache=50, C=.1, tol=0.01)

tree_ssvm = OneSlackSSVM(tree_model, inference_cache=50, C=.1, tol=0.01)

independent_ssvm = OneSlackSSVM(independent_model, C=.1, tol=0.01)

print("fitting independent model...")
independent_ssvm.fit(X_train, y_train)
print("fitting full model...")
full_ssvm.fit(X_train, y_train)
print("fitting tree model...")
tree_ssvm.fit(X_train, y_train)

print("Training loss independent model: %f"
      % hamming_loss(y_train, np.vstack(independent_ssvm.predict(X_train))))
print("Test loss independent model: %f"
      % hamming_loss(y_test, np.vstack(independent_ssvm.predict(X_test))))

print("Training loss tree model: %f"
      % hamming_loss(y_train, np.vstack(tree_ssvm.predict(X_train))))
print("Test loss tree model: %f"
      % hamming_loss(y_test, np.vstack(tree_ssvm.predict(X_test))))

print("Training loss full model: %f"
      % hamming_loss(y_train, np.vstack(full_ssvm.predict(X_train))))
print("Test loss full model: %f"
      % hamming_loss(y_test, np.vstack(full_ssvm.predict(X_test))))