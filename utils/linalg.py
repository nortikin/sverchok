# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

"""
Linear algebra routines.

These are mostly wrappers around numpy.linalg and scipy.sparse.linalg, but also
some algorithms built on them.
"""

import numpy as np

from sverchok.core.sv_custom_exceptions import SvInvalidInputException, SvInvalidResultException
from sverchok.utils.sv_logging import get_logger
from sverchok.dependencies import scipy

SIZE_THRESHOLD = 200
DENSITY_THRESHOLD = 0.1

def solve_dense(A, B):
    return np.linalg.solve(A, B)

def least_squares_dense(A, B):
    x, residues, rank, singval = np.linalg.lstsq(A, B, rcond=None)
    return x, residues.sum()

def use_sparse(A):
    m, n = A.shape[0], A.shape[1]
    if m >= SIZE_THRESHOLD or n >= SIZE_THRESHOLD:
        nonzero = np.count_nonzero(A)
        density = nonzero / (m*n)
        #print(f"Size {m}x{n}, density {density}")
        if density <= DENSITY_THRESHOLD:
            return True
    return False

if scipy is None:
    def solve_sparse(A, B):
        return np.linalg.solve(A, B)

    def least_squares_sparse(A, B):
        x, residues, rank, singval = np.linalg.lstsq(A, B, rcond=None)
        return x, residues.sum()
else:
    def solve_sparse(A, B):
        if use_sparse(A):
            #print("Solve sparse")
            A = scipy.sparse.csr_matrix(A)
            return scipy.sparse.linalg.spsolve(A, B)
        else:
            #print("Solve dense")
            return np.linalg.solve(A, B)
    
    def least_squares_sparse(A, B):
        if use_sparse(A):
            #print("Least squares sparse")
            A = scipy.sparse.csr_matrix(A)
            x, istop, itn, normr, normar, norma, noda, normx = scipy.sparse.linalg.lsmr(A, B)
            #print(f" => X {x.shape}")
            return x[np.newaxis].T, normr
        else:
            #print("Least squares dense")
            x, residues, rank, singval = np.linalg.lstsq(A, B, rcond=None)
            #print(f" => X {x.shape}")
            return x, residues.sum()

def least_squares_with_constraints(A, B, constraints_A, constraints_B,
                                   constraints_tolerance = 1e-6,
                                   use_svd_condition_threshold = 1000,
                                   logger = None):
    """
    Solve least squares problem with linear constraints, that must be satisfied exactly.

    This method will find a vector X, such that equations A X = B are either
    satisfied or almost satisfied (with minimum possible error), and, at the
    same time, equations constraints_A X = constraints_B are satisfied exactly.

    Args:
        A, B: equation matrices for least squares method, as for np.linalg.lstsq method.
        constraints_A, constraints_B: equation matrices for exact consrtaints.
        constraints_tolerance: if it occurs that for some reason constraints
            are satisfied with precision worse than this tolerance, the method will
            raise an exception. Pass None to save time by bypassing this check.
        use_svd_condition_threshold: threshold for constraints matrix condition
            number; if it is bigger than threshold, the metohd switches to use of
            SVD algorithm.

    Returns:
        Tuple:
            x: solution vector
            residue: sum of errors
    """
    if logger is None:
        logger = get_logger()

    A1, B1 = constraints_A, constraints_B
    A2, B2 = A, B
    if A1.shape[0] > A1.shape[1]:
        raise SvInvalidInputException(f"Number of constraints {A1.shape[0]} is bigger than number of unknowns {A1.shape[1]}")
    x_p, residue_x_p, _, _ = np.linalg.lstsq(A1, B1, rcond=None)
    #logger.info(f"A1 {A1.shape}, B1 {B1.shape}, A2 {A2.shape}, B2 {B2.shape} => x_p {x_p.shape}")
    if not np.allclose(A1 @ x_p, B1):
        raise SvInvalidInputException("Constraints are inconsistent")

    M = A1 @ A1.T
    cond_M = np.linalg.cond(M)
    use_svd = cond_M > use_svd_condition_threshold
    logger.debug("Condition number of constraints = %s; use SVD: %s", cond_M, use_svd)
    if use_svd:
        _U, singvalues, Vt = np.linalg.svd(A1, full_matrices=True)
        singval_tolerance = max(A1.shape) * np.amax(singvalues) * np.finfo(singvalues.dtype).eps
        rank = np.sum(singvalues > singval_tolerance)

        V_null = Vt[rank:].T # (m, m-rank)
        A2_proj = A2 @ V_null
        B2_proj = B2 - A2 @ x_p
        z, residue_z = least_squares_sparse(A2_proj, B2_proj)
        delta = V_null @ z
    else:
        V = A2 @ A1.T
        try:
            Y = np.linalg.solve(M, V.T).T
        except np.linalg.LinAlgError as e:
            raise SvInvalidInputException(f"Constraints are linearly dependent: {e}") from e

        A2_proj = A2 - Y @ A1
        B2_proj = B2 - A2 @ x_p

        z, residue_z = least_squares_sparse(A2_proj, B2_proj)

        w = np.linalg.solve(M, A1 @ z)
        delta = z - A1.T @ w

    x = x_p + delta
    residue = residue_x_p.sum() + residue_z

    if constraints_tolerance is not None:
        diffs = A1 @ x - B1
        diff = (diffs * diffs).sum()
        logger.debug("Reached constraints precision: %s", diff)
        if diff > constraints_tolerance:
            raise SvInvalidResultException(f"Reached precision is too bad: {diff}; are constraints too strict?")

    return x, residue

