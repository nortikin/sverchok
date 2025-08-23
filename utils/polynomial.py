# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np
from math import pi

from sverchok.utils.math import binomial_array

COEFF_TYPES = (int,float, np.float64, np.ndarray)

class Polynomial:
    def __init__(self, coeffs):
        self.coeffs = np.asarray(coeffs, dtype=np.float64)

    def __repr__(self):
        def monomial(c,d):
            if c == 0:
                return ""
            elif d == 0:
                return str(c)
            elif c == 1.0:
                return "x^" + str(d)
            else:
                return f"{c}*x^{d}"
        monomials = [monomial(c,i) for i,c in enumerate(self.coeffs)]
        return " + ".join(reversed(monomials))

    @staticmethod
    def Constant(k, ndim=None):
        if ndim is None:
            shape = (1,)
        else:
            shape = (1,ndim)
        coeffs = np.zeros(shape)
        if len(shape) == 2:
            coeffs[0,:] = k
        elif len(shape) == 1:
            coeffs[0] = k
        else:
            raise ValueError(f"Unsupported shape: {shape}")
        return Polynomial(coeffs)

    @staticmethod
    def Zero(ndim=None):
        return Polynomial.Constant(0, ndim=ndim)

    @staticmethod
    def Monomial(coefficient=1.0, degree=1, ndim=None):
        if ndim is None:
            shape = (degree+1,)
        else:
            shape = (degree+1,ndim)
        coeffs = np.zeros(shape)
        if len(shape) == 1:
            coeffs[degree] = coefficient
        elif len(shape) == 2:
            coeffs[degree,:] = coefficient
        else:
            raise ValueError(f"Unsupported shape: {shape}")
        return Polynomial(coeffs)

    @staticmethod
    def Binomial(k, c, degree=1, ndim=None):
        if degree == 0:
            return Polynomial.Constant(1, ndim=ndim)
        elif degree == 1:
            return Polynomial.Constant(c, ndim=ndim) + Polynomial.Monomial(k, ndim=ndim)
        C = binomial_array(degree+1)
        if ndim is None:
            shape = (degree+1,)
        else:
            shape = (degree+1,ndim)
        coeffs = np.zeros(shape)
        if ndim is None:
            coeffs[:] = C[degree,:]
        else:
            for i in range(coeffs.shape[-1]):
                coeffs[:,i] = C[degree,:]
        j = np.arange(degree+1)
        if ndim is not None:
            j = j[np.newaxis].T
        #    k = np.full((1,ndim), k)
        coeffs *= k ** j
        coeffs *= c ** (degree - j)
        return Polynomial(coeffs)

    def get_degree(self):
        return len(self.coeffs) - 1

    def get_ndim(self):
        if self.coeffs.ndim == 1:
            return None
        else:
            return self.coeffs.shape[-1]

    def evaluate(self, x):
        n = len(self.coeffs)
        ds = np.arange(n)
        return (self.coeffs * x ** ds).sum()

    def evaluate_array(self, xs):
        n = len(self.coeffs)
        ds = np.arange(n)
        if self.get_ndim() is None:
            xs = xs[np.newaxis].T
            return (self.coeffs * xs ** ds).sum(axis=1)
        else:
            #print("X", xs, ds)
            xs = xs[np.newaxis].T ** ds
            xs = np.transpose(xs[np.newaxis], axes=(1,2,0))
            #xs = xs[np.newaxis]
            #coeffs = np.transpose(self.coeffs[np.newaxis], axes=(1,2,0))
            coeffs = self.coeffs[np.newaxis]
            #print(f"X* {coeffs.shape} {xs.shape}")
            xs = coeffs * xs
            #print("Sum shape", xs.shape)
            xs = xs.sum(axis=1)
            #print("X shape", xs.shape)
            return xs

    def linear_substitute(self, k, c):
        poly = Polynomial.Zero(ndim=self.get_ndim())
        for i, a in enumerate(self.coeffs):
            poly = poly + Polynomial.Binomial(k, c, degree=i, ndim=self.get_ndim()) * a
        return poly

    def scale(self, scalar):
        if isinstance(scalar, (int, float, np.float64)):
            return Polynomial(scalar * self.coeffs)
        elif isinstance(scalar, np.ndarray) and scalar.ndim == 1:
            coeffs = scalar[np.newaxis] * self.coeffs
            return Polynomial(coeffs)
        else:
            raise TypeError("Unsupported argument types")

    def negate(self):
        return Polynomial(-1 * self.coeffs)

    def add(self, other):
        if isinstance(other, COEFF_TYPES):
            other = Polynomial.Constant(other, ndim=self.get_ndim())
        if self.coeffs.ndim != other.coeffs.ndim:
            raise ValueError(f"Incompatible polynomial shapes: {self.get_ndim()} vs {other.get_ndim()}")
        n = max(len(self.coeffs), len(other.coeffs))
        if self.coeffs.ndim == 1:
            coeffs = np.zeros((n,))
            coeffs[:len(self.coeffs)] += self.coeffs
            coeffs[:len(other.coeffs)] += other.coeffs
            return Polynomial(coeffs)
        elif self.coeffs.ndim == 2:
            shape = list(self.coeffs.shape)
            shape[0] = n
            coeffs = np.zeros(shape)
            coeffs[:len(self.coeffs),:] += self.coeffs
            coeffs[:len(other.coeffs),:] += other.coeffs
            return Polynomial(coeffs)
        else:
            raise TypeError("Unsupported argument types")

    def __add__(self, other):
        return self.add(other)

    def __sub__(self, other):
        if isinstance(other, COEFF_TYPES):
            other = Polynomial.Constant(other, ndim=self.get_ndim())
        return self.add(other.negate())

    def __mul__(self, other):
        if isinstance(other, COEFF_TYPES):
            return self.scale(other)
        if other.get_degree() == 1:
            n = len(self.coeffs)
            shape = list(self.coeffs.shape)
            shape[0] = n+1
            coeffs = np.zeros(shape)
            coeffs[1:] = self.coeffs
            coeffs *= other.coeffs[1]
            return Polynomial(coeffs) + Polynomial(other.coeffs[0] * self.coeffs)
        raise ValueError(f"Multiplication by arbitrary degree polynomial is not implemented yet: {self.coeffs.shape} x {other.coeffs.shape}")

    def roughen(self, tolerance):
        sums = np.cumsum(abs(self.coeffs[::-1]))
        k = sums.searchsorted(tolerance)
        n = len(self.coeffs)
        return Polynomial(self.coeffs[:n-k])

    def truncate(self, max_degree):
        n = min(len(self.coeffs), max_degree+1)
        return Polynomial(self.coeffs[:n])

def lagrange_basis(n, i, xs, ndim=None):
    poly = Polynomial.Constant(1, ndim=ndim)
    x = Polynomial.Monomial(ndim=ndim)
    for j in range(n):
        if i == j:
            continue
        p = (x - xs[j]) * (1.0/(xs[i] - xs[j]))
        #print(f"P[{i},{j}]: (x - {xs[j]}) / ({xs[i] - xs[j]})")
        poly = poly * p
    return poly

def chebyshev_nodes(n):
    ks = np.arange(1, n+1)
    xs = (2*ks - 1)*pi/(2*n)
    return np.cos(xs)[::-1]

def chebyshev_nodes_transform(tknots):
    t_min = tknots[0]
    t_max = tknots[-1]
    n = len(tknots)
    ks = (n-1) * (tknots - t_min) / (t_max - t_min) + 1
    xs = (2*ks - 1)*pi/(2*n)
    return np.cos(xs)[::-1]

def chebyshev_T(n, ndim=None):
    if n == 0:
        return Polynomial.Constant(1.0, ndim=ndim)
    elif n == 1:
        return Polynomial.Monomial(ndim=ndim)
    else:
        tn1 = chebyshev_T(n-1, ndim=ndim)
        tn2 = chebyshev_T(n-2, ndim=ndim)
        return tn1 * Polynomial.Monomial(coefficient=2, ndim=ndim) - tn2

def legendre_P(n, ndim=None):
    if n == 0:
        return Polynomial.Constant(1.0, ndim=ndim)
    elif n == 1:
        return Polynomial.Monomial(ndim=ndim)
    else:
        pn1 = legendre_P(n-1, ndim=ndim)
        pn2 = legendre_P(n-2, ndim=ndim)
        poly = pn1 * Polynomial.Monomial(2*n-1, degree=1, ndim=ndim)
        poly = poly - pn2*(n-1)
        poly = poly * (1.0 / n)
        return poly

def polynomial_interpolate(basis, xs, ys, max_degree=None, tolerance=None):
    n = len(xs)

    if max_degree is None:
        degree = n
    else:
        degree = min(max_degree, n)

    if ys.ndim == 1:
        ndim = None
        A = np.zeros((n, degree))
    else:
        ndim = ys.shape[-1]
        A = np.zeros((ndim, n, degree))

    polys = [basis(i, ndim=ndim) for i in range(degree)]
    for i in range(degree):
        if ndim is None:
            A[:,i] = polys[i].evaluate_array(xs)
        else:
            A[:,:,i] = polys[i].evaluate_array(xs).T
    if degree == n:
        ks = np.linalg.solve(A, ys.T).T
    else:
        if ndim is None:
            ks, residuals, rank, s = np.linalg.lstsq(A, ys.T)
        else:
            ks, residuals, rank, s = np.linalg.lstsq(A[0], ys)

    if tolerance is not None:
        sums = np.cumsum(abs(ks[::-1]), axis=0)
        sums = sums.max(axis=1)
        k = sums.searchsorted(tolerance)
        #print("Ks", ks, sums, k)
        if k > 0:
            print("K delta:", abs(ks[-k:]).sum(axis=0), k)
            ks = ks[:-k]

    solution = Polynomial.Zero(ndim=ndim)
    for i,k in enumerate(ks):
        solution = solution + polys[i] * k
    return solution

def chebyshev_T_interpolate(xs,ys, max_degree=None, tolerance=None):
    return polynomial_interpolate(chebyshev_T, xs, ys, max_degree=max_degree, tolerance=tolerance)

def legendre_interpolate(xs,ys, max_degree=None, tolerance=None):
    return polynomial_interpolate(legendre_P, xs, ys, max_degree=max_degree, tolerance=tolerance)

