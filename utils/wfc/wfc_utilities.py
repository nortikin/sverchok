"""Utility data and functions for WFC"""

import collections

import numpy as np

CoordXY = collections.namedtuple('coords_xy', ['x','y'])
CoordRC = collections.namedtuple('coords_rc', ['row','column'])


def hash_downto(a, rank, seed=0):
    state = np.random.RandomState(seed)
    assert rank < len(a.shape)
    #print((np.prod(a.shape[:rank]),-1))
    #print(np.array([np.prod(a.shape[:rank]),-1], dtype=np.int64).dtype)
    u = a.reshape(np.array([np.prod(a.shape[:rank]),-1], dtype=np.int64)) # change because lists are by default float64?
    #u = a.reshape((np.prod(a.shape[:rank]),-1))
    v = state.randint(1-(1<<63), 1<<63, np.prod(a.shape[rank:]),dtype='int64')
    return np.inner(u,v).reshape(a.shape[:rank]).astype('int64')
