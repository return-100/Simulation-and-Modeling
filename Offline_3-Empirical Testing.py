import numpy as np
import math as math
from scipy import stats


class RandomNumberTester:
    def __init__(self, seed, n, alpha):
        self.seed = seed
        self.n = n
        self.z = []
        self.u = []
        self.alpha = alpha
        self.mapping = {}
        self.a = [[4529.4, 9044.9, 13568, 18091, 22615, 27892],
                  [9044.9, 18097, 27139, 36187, 45234, 55789],
                  [13568, 27139, 40721, 54281, 67852, 83685],
                  [18091, 36187, 54281, 72414, 90470, 111580],
                  [22615, 45234, 67852, 90470, 113262, 139476],
                  [27892, 55789, 83685, 111580, 139476, 172860]]
        self.b = [1 / 6, 5 / 24, 11 / 120, 19 / 720, 29 / 5040, 1 / 840]

    def generate_random_number(self):
        for i in range(self.n):
            if i == 0:
                self.z.append(self.seed)
            else:
                self.z.append(int(65539 * self.z[i - 1]) % 2 ** 31)
            self.u.append(self.z[i] / 2 ** 31)

    def uniformity_test(self, k):
        f = []
        summation = 0.0
        for i in range(k):
            f.append(0)
        for i in range(self.n):
            f[int(self.u[i] * k)] += 1
        for i in range(k):
            summation += (float(f[i]) - float(self.n / k)) ** 2
        chi2 = summation * float(k / self.n)
        if chi2 > stats.chi2.ppf(q=1 - self.alpha, df=k - 1):
            print("Chi2 =", chi2, "ppf =", stats.chi2.ppf(q=1 - self.alpha, df=k - 1), "Rejected")
        else:
            print("Chi2 =", chi2, "ppf =", stats.chi2.ppf(q=1 - self.alpha, df=k - 1), "Not rejected")

    def generate_all_sequence(self, d, k, pattern):
        if d:
            for i in range(k):
                self.generate_all_sequence(d - 1, k, pattern + str(i))
        else:
            self.mapping[pattern] = 0

    def serial_test(self, d, k):
        summation = 0
        self.mapping = {}
        self.generate_all_sequence(d, k, "")
        for i in range(math.floor(self.n / d)):
            pattern = ""
            for j in range(i * d, (i * d) + d):
                pattern += str(int(self.u[j] * k))
            self.mapping[pattern] += 1
        l = math.floor(self.n / d)
        for key in self.mapping:
            summation += (self.mapping[key] - (l / k ** d)) ** 2
        chi2 = summation * (k ** d / l)
        if chi2 > stats.chi2.ppf(q=1 - self.alpha, df=pow(k, d) - 1):
            print("Chi2 =", chi2, "ppf =", stats.chi2.ppf(q=1 - self.alpha, df=pow(k, d) - 1), "Rejected")
        else:
            print("Chi2 =", chi2, "ppf =", stats.chi2.ppf(q=1 - self.alpha, df=pow(k, d) - 1), "Not rejected")

    def runs_test(self):
        r = []
        cur_length = 1
        summation = 0
        for i in range(6):
            r.append(0)
        for i in range(1, self.n):
            if self.u[i] >= self.u[i - 1]:
                cur_length += 1
            else:
                r[min(5, cur_length - 1)] += 1
                cur_length = 1
            if i == self.n - 1:
                r[min(5, cur_length - 1)] += 1
        print(r)
        for i in range(6):
            for j in range(6):
                summation += self.a[i][j] * (r[i] - self.n * self.b[i]) * (r[j] - self.n * self.b[j])
        R = (1.0 / self.n) * summation
        if R > stats.chi2.ppf(q=1 - self.alpha, df=6):
            print("R =", R, "ppf =", stats.chi2.ppf(q=1 - self.alpha, df=6), "Rejected")
        else:
            print("R =", R, "ppf =", stats.chi2.ppf(q=1 - self.alpha, df=6), "Not rejected")

    def correlation_test(self, j):
        rho = 0
        h = math.floor(((self.n - 1) / j) - 1)
        for k in range(h + 1):
            rho += self.u[k * j] * self.u[(k + 1) * j]
        rho = ((12 / (h + 1)) * rho) - 3
        variance = (13 * h + 7) / (h + 1)**2
        A = rho / math.sqrt(variance)
        if abs(A) > stats.norm.ppf(q=1 - self.alpha / 2):
            print("A =", abs(A), "ppf =", stats.norm.ppf(q=1 - self.alpha / 2), "Rejected")
        else:
            print("A =", abs(A), "ppf =", stats.norm.ppf(q=1 - self.alpha / 2), "Not rejected")


if __name__ == "__main__":
    for n in [20, 500, 4000, 10000]:
        print("N=", n, "\n")

        rndtest = RandomNumberTester(1505100, n, 0.1)
        rndtest.generate_random_number()

        print("Uniformity Testing")
        for k in [10, 20]:
            print("k=", k)
            rndtest.uniformity_test(k)
        print("\n")

        print("Serial Testing")
        for d in [2, 3]:
            for k in [4, 8]:
                print("d=", d, "k=", k)
                rndtest.serial_test(d, k)
        print("\n")

        print("Runs test")
        rndtest.runs_test()
        print("\n")

        print("Correlation Testing")
        for j in [1, 3, 5]:
            print("j=", j)
            rndtest.correlation_test(j)
        print("\n")
