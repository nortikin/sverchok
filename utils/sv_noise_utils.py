# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import numpy as np

noise_options = [
    ('BLENDER', 0),
    ('PERLIN_ORIGINAL', 1),
    ('PERLIN_NEW', 2),
    ('VORONOI_F1', 3),
    ('VORONOI_F2', 4),
    ('VORONOI_F3', 5),
    ('VORONOI_F4', 6),
    ('VORONOI_F2F1', 7),
    ('VORONOI_CRACKLE', 8),
    ('CELLNOISE', 14)
]

def get_noise_type(name):
    return dict(noise_options)[name]

for name, value in noise_options:
    locals()[name] = name

#### #Numpy noises

PERLIN_VECS = np.array([
    [1, 1, 0], [-1, 1, 0], [1, -1, 0], [-1, -1, 0],
    [1, 0, 1], [-1, 0, 1], [1, 0, -1], [-1, 0, -1],
    [0, 1, 1], [0, -1, 1], [0, 1, -1], [0, -1, -1],
    ])/np.sqrt(2)

ORTHO_VECS = np.array([
    [1, 0, 0], [0, 1, 0], [0, 0, 1],
    [-1, 0, 0], [0, -1, 0], [0, 0, -1]
    ])
OFFSET_VECS = np.array([
    [1, 0, 0],
    [0, 1, 0], [1, 1, 0],
    [0, 0, 1], [1, 0, 1],
    [0, 1, 1], [1, 1, 1]])

def rand(scalar_array, seed):
    ''' pseudo random from scalar. Returns the fractional part of the sin formula'''
    return np.modf(seed*np.sin(scalar_array))[0]

def rand_v(vector_array, seed_vals):
    '''
    pseudo random from vector.
    Returns the fractional part of the sin formula
    seed_vals is an array with 7 random numbers'''
    c = seed_vals
    s = np.sum(vector_array * c[:3], axis=1)
    return 0.5 + 0.5 * np.modf(c[3] * np.sin(c[4] * rand(s, c[5]) + c[6]))[0]

def rand_vector_from_v(vector_array, seed_vals):
    '''
    pseudo random from vector.
    Returns the fractional part of the sin formula
    seed_vals is an array with 7 random numbers'''
    c = seed_vals
    s = np.sum(vector_array * c[:3], axis=1)
    return np.stack((
        np.modf(c[3] * np.sin(c[4] * rand(s, c[5]) + c[6]))[0],
        np.modf(c[4] * np.sin(c[5] * rand(s, c[6]) + c[3]))[0],
        np.modf(c[5] * np.sin(c[6] * rand(s, c[3]) + c[4]))[0])
        ).T

def perlin_ease(v):
    '''array easing from perlin noise'''
    return 6 * np.power(v, 5) - 15 * np.power(v, 4)+ 10 * np.power(v, 3)

def interp(v1, v2, fac):
    '''array interpolation'''
    return v1 + (v2 - v1) * fac

def multi_interpolation(gradients, v_frac):
    '''interpolate between 8 gradients using x,y and z values '''
    return interp(
                interp(
                    interp(gradients[0], gradients[1], v_frac[:, 0]),
                    interp(gradients[2], gradients[3], v_frac[:, 0]),
                    v_frac[:, 1]
                    ),
                interp(
                    interp(gradients[4], gradients[5], v_frac[:, 0]),
                    interp(gradients[6], gradients[7], v_frac[:, 0]),
                    v_frac[:, 1]
                    ),
                v_frac[:, 2]
                )

def choose_vector(rand_vecs, v_int, seed_vals):
    return rand_vecs[(rand_vecs.shape[0] * rand_v(v_int, seed_vals)).astype(int)]

def random_vector(rand_vecs, v_int, seed_vals):
    return rand_vecs[(rand_vecs.shape[0] * rand_v(v_int, seed_vals)).astype(int)]

def gradient_noise_random(vecs, seed, smooth):
    '''sets random seed and passes random vectors to the noise gradients func'''
    np.random.seed(seed)
    rand_vecs = np.random.uniform(-1, 1, (64, 3))
    rand_vecs /= np.linalg.norm(rand_vecs, axis=1)[:, np.newaxis]
    return noise_gradients(vecs, smooth, rand_vecs)

def gradient_noise_ortho(vecs, seed, smooth):
    '''sets random seed and passes ortho vectors to the noise gradients func'''

    np.random.seed(seed)
    rand_vecs = np.repeat(ORTHO_VECS, 2, axis=0)
    rand_vecs = ORTHO_VECS
    return noise_gradients(vecs, smooth, rand_vecs)

def gradient_noise_perlin(vecs, seed, smooth):
    '''sets random seed and passes perlin vectors to the noise gradients func'''

    np.random.seed(seed)
    return noise_gradients(vecs, smooth, PERLIN_VECS)


def noise_gradients(vecs, smooth, rand_vecs):
    '''the gradient is a dot product between a random vector and the fractional part of the vector'''
    seed_vals = np.random.uniform(10, 10000, 7)
    v_int = np.floor(vecs)
    if smooth:
        v_frac = perlin_ease(vecs - v_int)
    else:
        v_frac = vecs - v_int

    gradient = np.sum(choose_vector(rand_vecs, v_int, seed_vals) * v_frac, axis=1)

    return (1 + gradient)*.5



def interpolation_noise_random(vecs, seed, smooth):
    '''sets random seed and passes random vectors to the noise noise_interpolator func'''
    np.random.seed(seed)
    rand_vecs = np.random.uniform(-1, 1, (12, 3))
    rand_vecs /= np.linalg.norm(rand_vecs, axis=1)[:, np.newaxis]
    return random_gradient_interpolator(vecs, smooth, rand_vecs)

def interpolation_noise_ortho(vecs, seed, smooth):
    '''sets random seed and passes ortho vectors to the noise noise_interpolator func'''

    np.random.seed(seed)
    rand_vecs = np.repeat(ORTHO_VECS, 2, axis=0)
    return noise_interpolator(vecs, smooth, rand_vecs)

def numpy_perlin_noise(vecs, seed, smooth):
    '''sets random seed and passes  Perlin vectors to the noise noise_interpolator func'''
    np.random.seed(seed)
    return noise_interpolator(vecs, smooth, PERLIN_VECS)


def noise_interpolator(vecs, smooth, rand_vecs):
    '''
    Interpolate between gradients.
    The gradient is a dot product between a random vector
    and the fractional part of the vector
    rand_vecs in one array with 12 vectors
    '''
    seed_vals = np.random.uniform(10, 10000, 7)
    offset = OFFSET_VECS
    v_int = np.floor(vecs)
    v_frac = vecs - v_int
    gradients = [np.sum(choose_vector(rand_vecs, v_int, seed_vals) * v_frac, axis=1)]
    for off in offset:
        gradients.append(
            np.sum(choose_vector(rand_vecs, v_int + off, seed_vals) *  (v_frac- off), axis=1)
        )

    if smooth:
        r_total = 0.5 + multi_interpolation(gradients, perlin_ease(v_frac))
    else:
        r_total = 0.5 + multi_interpolation(gradients, v_frac)

    return r_total

def random_gradient_interpolator(vecs, smooth, rand_vecs):
    '''
    Interpolate between gradients.
    The gradient is a dot product between a random vector
    and the fractional part of the vector
    rand_vecs in one array with 12 vectors
    '''
    seed_vals = np.random.uniform(10, 10000, 7)
    offset = OFFSET_VECS
    v_int = np.floor(vecs)
    v_frac = vecs - v_int

    gradients = [np.sum(choose_vector(rand_vecs, v_int, seed_vals) * v_frac, axis=1)]

    for off in offset:
        gradients.append(
            np.sum(choose_vector(rand_vecs, v_int + off, seed_vals) *  (v_frac- off), axis=1)
        )

    if smooth:
        r_total = 0.5 + multi_interpolation(gradients, perlin_ease(v_frac))
    else:
        r_total = 0.5 + multi_interpolation(gradients, v_frac)

    return r_total


def random_interpolator(vecs, seed, smooth):
    '''
    Interpolate between values.
    The value is random value at each integer
    the fractional part of the vector is used to make the interpolation.
    rand_vecs in one array with 12 vectors
    '''
    np.random.seed(seed)
    seed_vals = np.random.uniform(10, 10000, 7)
    offset = OFFSET_VECS
    v_int = np.floor(vecs)
    v_frac = vecs - v_int

    gradients = [rand_v(v_int, seed_vals)]
    for off in offset:
        gradients.append(rand_v(v_int + off, seed_vals))
    if smooth:
        r_total = multi_interpolation(gradients, perlin_ease(v_frac))
    else:
        r_total = multi_interpolation(gradients, v_frac)

    return r_total

def random_cells(vecs, seed, smooth):
    '''The value is random value at each integer'''
    np.random.seed(seed)
    seed_vals = np.random.uniform(10, 10000, 7)

    return rand_v(np.floor(vecs), seed_vals)

noise_numpy_types = {
    'RANDOM_CELLS': (random_cells, random_interpolator),
    'RANDOM_GRADIENTS': (gradient_noise_random, interpolation_noise_random),
    'ORTHO_GRADIENTS': (gradient_noise_ortho, interpolation_noise_ortho),
    'NUMPY_PERLIN': (gradient_noise_perlin, numpy_perlin_noise),
     }
