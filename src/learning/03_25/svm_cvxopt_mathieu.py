import numpy as np
from numpy import linalg
import cvxopt
import cvxopt.solvers
import pandas as pd
import pickle
import sklearn.linear_model

def linear_kernel(x1, x2):
    return np.dot(x1, x2)

def rbf_kernel(F_1, F_2, sigma_2=1.0):
    return np.exp(-0.5*np.linalg.norm(F_1 - F_2)**2 / sigma_2)

def polynomial_kernel(x, y, p=3):
    return (1 + np.dot(x, y)) ** p


def gaussian_kernel(x, y, sigma=5.0):
    return np.exp(-linalg.norm(x - y) ** 2 / (2 * (sigma ** 2)))


class SVM(object):
    def __init__(self, kernel=rbf_kernel, C=None):
        self.kernel = kernel
        self.C = C
        if self.C is not None: self.C = float(self.C)

    def fit(self, X, y):
        n_samples, n_features = X.shape

        # Gram matrix
        K = np.zeros((n_samples, n_samples))
        for i in range(n_samples):
            for j in range(n_samples):
                K[i, j] = self.kernel(X[i], X[j])

        P = cvxopt.matrix(np.outer(y, y) * K)
        q = cvxopt.matrix(np.ones(n_samples) * -1)
        A = cvxopt.matrix(y, (1, n_samples))
        b = cvxopt.matrix(0.0)

        opt = cvxopt.solvers.options['show_progress'] = False
        if self.C is None:
            G = cvxopt.matrix(np.diag(np.ones(n_samples) * -1))
            h = cvxopt.matrix(np.zeros(n_samples))
        else:
            tmp1 = np.diag(np.ones(n_samples) * -1)
            tmp2 = np.identity(n_samples)
            G = cvxopt.matrix(np.vstack((tmp1, tmp2)))
            tmp1 = np.zeros(n_samples)
            tmp2 = np.ones(n_samples) * self.C
            h = cvxopt.matrix(np.hstack((tmp1, tmp2)))

        # solve QP problem
        solution = cvxopt.solvers.qp(P, q, G, h, A, b)

        # Lagrange multipliers
        a = np.ravel(solution['x'])
        print(a)
        # Support vectors have non zero lagrange multipliers
        sv = a > 1e-3
        # print(a[sv])
        ind = np.arange(len(a))[sv]
        # print(X.shape)
        print(a.shape)
        self.a = a[sv]
        print(self.a.shape)
        self.sv = X[sv]
        self.sv_y = y[sv]
        # print("%d support vectors out of %d points" % (len(self.a), n_samples))

        # Intercept
        self.b = 0
        for n in range(len(self.a)):
            self.b += self.sv_y[n]
            self.b -= np.sum(self.a * self.sv_y * K[ind[n], sv])
        self.b /= len(self.a)

        # Weight vector
        if self.kernel == linear_kernel:
            self.w = np.zeros(n_features)
            for n in range(len(self.a)):
                self.w += self.a[n] * self.sv_y[n] * self.sv[n]
        else:
            self.w = None

    def project(self, X):
        if self.w is not None:
            return np.dot(X, self.w) + self.b
        else:
            y_predict = np.zeros(len(X))
            for i in range(len(X)):
                s = 0
                print(self.a.shape)
                for a, sv_y, sv in zip(self.a, self.sv_y, self.sv):
                    # print(self.kernel(X[i], sv))
                    s += a * sv_y * self.kernel(X[i], sv)
                y_predict[i] = s

            print('B: ', self.b, y_predict)
            return y_predict + self.b

    def predict(self, X):
        return np.sign(self.project(X))


if __name__ == "__main__":
    import pylab as pl


    def gen_lin_separable_data():
        # generate training data in the 2-d case
        mean1 = np.array([0, 2])
        mean2 = np.array([2, 0])
        cov = np.array([[0.8, 0.6], [0.6, 0.8]])
        X1 = np.random.multivariate_normal(mean1, cov, 100)
        y1 = np.ones(len(X1))
        X2 = np.random.multivariate_normal(mean2, cov, 100)
        y2 = np.ones(len(X2)) * -1
        return X1, y1, X2, y2


    def gen_non_lin_separable_data():
        mean1 = [-1, 2]
        mean2 = [1, -1]
        mean3 = [4, -4]
        mean4 = [-4, 4]
        cov = [[1.0, 0.8], [0.8, 1.0]]
        X1 = np.random.multivariate_normal(mean1, cov, 50)
        X1 = np.vstack((X1, np.random.multivariate_normal(mean3, cov, 50)))
        y1 = np.ones(len(X1))
        X2 = np.random.multivariate_normal(mean2, cov, 50)
        X2 = np.vstack((X2, np.random.multivariate_normal(mean4, cov, 50)))
        y2 = np.ones(len(X2)) * -1
        return X1, y1, X2, y2


    def gen_lin_separable_overlap_data():
        # generate training data in the 2-d case
        mean1 = np.array([0, 2])
        mean2 = np.array([2, 0])
        cov = np.array([[1.5, 1.0], [1.0, 1.5]])
        X1 = np.random.multivariate_normal(mean1, cov, 100)
        y1 = np.ones(len(X1))
        X2 = np.random.multivariate_normal(mean2, cov, 100)
        y2 = np.ones(len(X2)) * -1
        return X1, y1, X2, y2


    def split_train(X1, y1, X2, y2):
        X1_train = X1[:90]
        y1_train = y1[:90]
        X2_train = X2[:90]
        y2_train = y2[:90]
        X_train = np.vstack((X1_train, X2_train))
        y_train = np.hstack((y1_train, y2_train))
        return X_train, y_train


    def split_test(X1, y1, X2, y2):
        X1_test = X1[90:]
        y1_test = y1[90:]
        X2_test = X2[90:]
        y2_test = y2[90:]
        X_test = np.vstack((X1_test, X2_test))
        y_test = np.hstack((y1_test, y2_test))
        return X_test, y_test


    def plot_margin(X1_train, X2_train, clf):
        def f(x, w, b, c=0):
            # given x, return y such that [x,y] in on the line
            # w.x + b = c
            return (-w[0] * x - b + c) / w[1]

        pl.plot(X1_train[:, 0], X1_train[:, 1], "ro")
        pl.plot(X2_train[:, 0], X2_train[:, 1], "bo")
        pl.scatter(clf.sv[:, 0], clf.sv[:, 1], s=100, c="g")

        # w.x + b = 0
        a0 = -4;
        a1 = f(a0, clf.w, clf.b)
        b0 = 4;
        b1 = f(b0, clf.w, clf.b)
        pl.plot([a0, b0], [a1, b1], "k")

        # w.x + b = 1
        a0 = -4;
        a1 = f(a0, clf.w, clf.b, 1)
        b0 = 4;
        b1 = f(b0, clf.w, clf.b, 1)
        pl.plot([a0, b0], [a1, b1], "k--")

        # w.x + b = -1
        a0 = -4;
        a1 = f(a0, clf.w, clf.b, -1)
        b0 = 4;
        b1 = f(b0, clf.w, clf.b, -1)
        pl.plot([a0, b0], [a1, b1], "k--")

        pl.axis("tight")
        pl.show()


    def plot_contour(X1_train, X2_train, clf):
        pl.plot(X1_train[:, 0], X1_train[:, 1], "ro")
        pl.plot(X2_train[:, 0], X2_train[:, 1], "bo")
        pl.scatter(clf.sv[:, 0], clf.sv[:, 1], s=100, c="g")

        X1, X2 = np.meshgrid(np.linspace(-6, 6, 50), np.linspace(-6, 6, 50))
        X = np.array([[x1, x2] for x1, x2 in zip(np.ravel(X1), np.ravel(X2))])
        Z = clf.project(X).reshape(X1.shape)
        pl.contour(X1, X2, Z, [0.0], colors='k', linewidths=1, origin='lower')
        pl.contour(X1, X2, Z + 1, [0.0], colors='grey', linewidths=1, origin='lower')
        pl.contour(X1, X2, Z - 1, [0.0], colors='grey', linewidths=1, origin='lower')

        pl.axis("tight")
        pl.show()


    def test_linear():
        X1, y1, X2, y2 = gen_lin_separable_data()
        X_train, y_train = split_train(X1, y1, X2, y2)
        X_test, y_test = split_test(X1, y1, X2, y2)

        clf = SVM()
        clf.fit(X_train, y_train)

        # y_predict = clf.predict(X_test)
        # correct = np.sum(y_predict == y_test)
        # print("%d out of %d predictions correct" % (correct, len(y_predict)))

        # plot_margin(X_train[y_train == 1], X_train[y_train == -1], clf)


    def test_non_linear():
        X1, y1, X2, y2 = gen_non_lin_separable_data()
        X_train, y_train = split_train(X1, y1, X2, y2)
        X_test, y_test = split_test(X1, y1, X2, y2)

        clf = SVM(polynomial_kernel)
        clf.fit(X_train, y_train)

        # y_predict = clf.predict(X_test)
        # correct = np.sum(y_predict == y_test)
        # print("%d out of %d predictions correct" % (correct, len(y_predict)))
        #
        # plot_contour(X_train[y_train == 1], X_train[y_train == -1], clf)


    def test_soft():
        X1, y1, X2, y2 = gen_non_lin_separable_data()
        X_train, y_train = split_train(X1, y1, X2, y2)
        # print(type(X_train))
        X_test, y_test = split_test(X1, y1, X2, y2)

        clf = SVM(C=1000.1)
        clf.fit(X_train, y_train)

        # y_predict = clf.predict(X_test)
        # correct = np.sum(y_predict == y_test)
        # print("%d out of %d predictions correct" % (correct, len(y_predict)))

        # plot_contour(X_train[y_train == 1], X_train[y_train == -1], clf)


    def test_custom():
        # forumsData = pd.read_csv('../../../darkweb_data/3_25/Forum40_labels.csv', encoding="ISO-8859-1")
        # forumsData = forumsData.fillna(value=0)
        # Y_labels = np.array(forumsData.ix[:, 3:14])
        # for idx in range(Y_labels.shape[0]):
        #     for idx_1 in range(Y_labels.shape[1]):
        #         if Y_labels[idx, idx_1] == 0.:
        #             Y_labels[idx, idx_1] = -1.
        #
        #
        # dir_feat = '../../../darkweb_data/3_25/features_d200/'
        # X_inst, Y_inst = pickle.load(open(dir_feat + 'feat_label_' + str(3) + '.pickle', 'rb'))
        # for idx_y in range(len(Y_inst)):
        #     if Y_inst[idx_y] == 0:
        #         Y_inst[idx_y] = -1.
        #     else:
        #         Y_inst[idx_y] = 1.
        #
        # X_inst = np.array(X_inst)
        # X_inst = np.squeeze(X_inst, axis=(1,))
        # Y_inst = np.array(Y_inst)
        #
        # X_train = X_inst[:380, :]
        # Y_train = Y_inst[:380]
        # # print(Y_train)
        # X_test = X_inst[380:, :]
        # Y_test = Y_inst[380:]

        input_dir = '../../../darkweb_data/05/5_19/data_test/v3/fold_' + str(0) + '/col_' + str(3) + '/'
        X_train = pickle.load(open(input_dir + 'X_train_l.pickle', 'rb'))
        Y_train_all = pickle.load(open(input_dir + 'Y_train_all.pickle', 'rb'))
        X_test = pickle.load(open('../../../darkweb_data/05/5_19/data_test/v3/fold_' + str(3) +
                                  '/' + 'X_test.pickle', 'rb'))
        Y_test_all = pickle.load(open('../../../darkweb_data/05/5_19/data_test/v3/fold_' + str(3) +
                                      '/' + 'Y_test_all.pickle', 'rb'))
        for idx_ind1 in range(Y_train_all.shape[0]):
            for idx_ind2 in range(Y_train_all.shape[1]):
                if Y_train_all[idx_ind1, idx_ind2] == 0.:
                    Y_train_all[idx_ind1, idx_ind2] = -1.

        Y_train = Y_train_all[:, 1]
        Y_test = Y_test_all[:, 1]

        clf = SVM(kernel=linear_kernel, C=1000.1)
        clf.fit(X_train, Y_train)

        print(X_train)

        y_predict = clf.predict(X_test)
        correct = np.sum(y_predict == Y_test)
        print("%d out of %d predictions correct" % (correct, len(y_predict)))

        clf = sklearn.linear_model.LogisticRegression()
        clf.fit(X_train, Y_train)
        y_predict = clf.predict(X_test)
        correct = np.sum(y_predict == Y_test)
        print("%d out of %d predictions correct" % (correct, len(y_predict)))

        # print(X_test.shape, Y_test.shape)


    # test_linear()
    # test_non_linear()
    # test_soft()
    test_custom()