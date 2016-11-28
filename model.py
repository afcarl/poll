'''
main algorithm
'''
from math import exp, sqrt
from random import random
class POLL(object):
    '''
    abstract class. Should never be called directly.
    '''
    def __init__(self, alpha, beta, L1, L2, D, interaction, interaction_dropout = 0.25):
        # parameters
        self.alpha = alpha
        self.beta = beta
        self.L1 = L1
        self.L2 = L2

        # feature related parameters
        self.D = D
        self.interaction = interaction
        self.interaction_dropout = interaction_dropout

        # model
        # n: squared sum of past gradients
        # z: weights
        # w: regularized weights
        # best_w: best w from epochs
        self.n = [0.] * D
        self.z = [0.] * D
        self.w = [0.] * D

    def _indices(self, x_row):
        ''' A helper generator that yields the indices in x per row

            The purpose of this generator is to make the following
            code a bit cleaner when doing feature interaction.
        '''

        # first yield index of the bias term
        yield 0

        # then yield the normal indices
        for fea in x_row:
            yield abs(hash(fea)) % self.D

        # now yield interactions (if applicable)
        if self.interaction:
            L = len(x_row)
            x_row = sorted(x_row)
            for i in xrange(L):
                for j in xrange(i+1, L):
                    # one-hot encode interactions with hash trick
                    i_field = int(x_row[i].split(":")[0])
                    j_field = int(x_row[j].split(":")[0])
                    #if i_field != j_field and j_field in range(5):  # 0.67911028862
                    if random() > self.interaction_dropout:
                        if i_field != j_field and j_field in range(4):   # 0.681464539227
                            yield abs(hash(str(x_row[i]) + '_' + str(x_row[j]))) % self.D

    def get_weights(self):
        '''
        get current weights
        '''
        return self.w



class LogLossLearner(POLL):

    def __init__(self, alpha, beta, L1, L2, D, interaction):
        super(LogLossLearner, self).__init__(alpha, beta, L1, L2, D, interaction)

    def predict(self, x, outside_weights = None):
        p = []
        for x_row in x:
            # parameters
            if outside_weights:
                w = outside_weights
            else:
                w = self.w

            # wTx is the inner product of w and x
            wTx = 0.
            for i in self._indices(x_row):
                wTx += w[i]

            p.append(1. / (1. + exp(-1.*wTx)))
        return p

    def update(self, x, p, y):
        '''
        x, p, y are lists
        '''
        assert len(x) == len(p)
        assert len(x) == len(y)
        for idx in xrange(len(x)):
            x_row, p_row, y_row = x[idx], p[idx], y[idx]
            # gradient under logloss
            g = p_row - y_row

            # update z and n
            for i in self._indices(x_row):
                sigma = (sqrt(self.n[i] + g * g) - sqrt(self.n[i])) / self.alpha
                self.z[i] += g - sigma * self.w[i]
                self.n[i] += g * g
                # regularize
                sign = -1. if self.z[i] < 0 else 1.
                if sign * self.z[i] <= self.L1:
                    self.w[i] = 0.
                else:
                    self.w[i] = (sign * self.L1 - self.z[i]) / ((self.beta + sqrt(self.n[i])) / self.alpha + self.L2)


class LambdaRankLearner(POLL):
    '''
    lambda rank optimizer
    '''

    def __init__(self, alpha, beta, L1, L2, D, interaction):
        super(LambdaRankLearner, self).__init__(alpha, beta, L1, L2, D, interaction)

    def predict(self, x, outside_weights=None):
        p = []
        for x_row in x:
            # parameters
            if outside_weights:
                w = outside_weights
            else:
                w = self.w

            # wTx is the inner product of w and x
            wTx = 0.
            for i in self._indices(x_row):
                wTx += w[i]

            #p.append(1. / (1. + exp(-1. * wTx))) # return probability
            p.append(wTx)  # return raw score
        return p


    def update(self, x, p, y):
        '''
        x, p, y are lists
        '''

        positive_index = y.index(1)
        s_pos = p[positive_index]
        g = [0] * len(x)
        for idx in xrange(len(x)):
            if y[idx] != 1:
                x_row, p_row, y_row = x[idx], p[idx], y[idx]
                g[idx] = 1./ (1. + exp(s_pos - p_row))
                # update z and n
                for i in self._indices(x_row):
                    sigma = (sqrt(self.n[i] + g[idx] * g[idx]) - sqrt(self.n[i])) / self.alpha
                    self.z[i] += g[idx] - sigma * self.w[i]
                    self.n[i] += g[idx] * g[idx]
                    # regularize
                    sign = -1. if self.z[i] < 0 else 1.
                    if sign * self.z[i] <= self.L1:
                        self.w[i] = 0.
                    else:
                        self.w[i] = (sign * self.L1 - self.z[i]) / (
                        (self.beta + sqrt(self.n[i])) / self.alpha + self.L2)

        # update the positive gradient
        grad_pos = -1 * sum(g)
        x_row, p_row, y_row = x[positive_index], p[positive_index], y[positive_index]
        for i in self._indices(x_row):
            sigma = (sqrt(self.n[i] + grad_pos * grad_pos) - sqrt(self.n[i])) / self.alpha
            self.z[i] += grad_pos - sigma * self.w[i]
            self.n[i] += grad_pos * grad_pos
            # regularize
            sign = -1. if self.z[i] < 0 else 1.
            if sign * self.z[i] <= self.L1:
                self.w[i] = 0.
            else:
                self.w[i] = (sign * self.L1 - self.z[i]) / (
                    (self.beta + sqrt(self.n[i])) / self.alpha + self.L2)

