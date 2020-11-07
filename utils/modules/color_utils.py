# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE
# pylint: disable=C0326

from mathutils import Color
import numpy as np

color_channels = {
    'Red':        (1, lambda x: x[0]),
    'Green':      (2, lambda x: x[1]),
    'Blue':       (3, lambda x: x[2]),
    'Hue':        (4, lambda x: Color(x[:3]).h),
    'Saturation': (5, lambda x: Color(x[:3]).s),
    'Value':      (6, lambda x: Color(x[:3]).v),
    'Alpha':      (7, lambda x: x[3]),
    'RGB Average':(8, lambda x: sum(x[:3])/3),
    'Luminosity': (9, lambda x: 0.21*x[0] + 0.72*x[1] + 0.07*x[2]),
    'Color': (10, lambda x: x[:3]),
    'RGBA': (11, lambda x: x[:]),
    }

def hsl_to_rgb(hsl_col):
    '''
    hsv_col has to be a 2 axis array with shape [:, 3]
    math taken from https://en.wikipedia.org/wiki/HSL_and_HSV
    '''
    rgb_col = np.zeros(hsl_col.shape)
    chroma = (1- np.abs(2 * hsl_col[:, 2]- 1)) * hsl_col[:, 1]
    h1f = (6 * hsl_col[:,0]) % 6
    x = chroma * (1 - np.abs((h1f % 2) - 1))
    h1 = np.floor(h1f).astype(int)

    m = hsl_col[:,2] - chroma/2
    zero = np.zeros(hsl_col.shape[0])

    h_0 = h1 == 0
    h_1 = h1 == 1
    h_2 = h1 == 2
    h_3 = h1 == 3
    h_4 = h1 == 4
    h_5 = h1 >= 5

    rgb_col[h_0,:] = np.stack((chroma[h_0], x[h_0], zero[h_0])).T
    rgb_col[h_1,:] = np.stack((x[h_1], chroma[h_1], zero[h_1])).T
    rgb_col[h_2,:] = np.stack((zero[h_2], chroma[h_2], x[h_2])).T
    rgb_col[h_3,:] = np.stack((zero[h_3], x[h_3], chroma[h_3])).T
    rgb_col[h_4,:] = np.stack((x[h_4], zero[h_4], chroma[h_4])).T
    rgb_col[h_5,:] = np.stack((chroma[h_5], zero[h_5], x[h_5])).T
    rgb_col += m[:,np.newaxis]
    return rgb_col


def hsv_to_rgb(hsv_col):
    '''
    hsv_col has to be a 2 axis array with shape [:, 3]
    math taken from https://en.wikipedia.org/wiki/HSL_and_HSV
    '''
    rgb_col = np.zeros(hsv_col.shape)
    h1 = np.floor(hsv_col[:, 0] * 6) % 6

    f = ((hsv_col[:,0]*6)%6 ) - h1
    p = hsv_col[:,2]*(1- hsv_col[:,1])
    q = hsv_col[:,2]*(1- f*hsv_col[:,1])
    t = hsv_col[:,2]*(1-(1-f)*hsv_col[:,1])
    v = hsv_col[:, 2]

    h_0 = h1 == 0
    h_1 = h1 == 1
    h_2 = h1 == 2
    h_3 = h1 == 3
    h_4 = h1 == 4
    h_5 = h1 == 5

    rgb_col[h_0, :] = np.stack((v[h_0], t[h_0], p[h_0])).T
    rgb_col[h_1,:] = np.stack((q[h_1], v[h_1], p[h_1])).T
    rgb_col[h_2,:] = np.stack((p[h_2], v[h_2], t[h_2])).T
    rgb_col[h_3,:] = np.stack((p[h_3], q[h_3], v[h_3])).T
    rgb_col[h_4,:] = np.stack((t[h_4], p[h_4], v[h_4])).T
    rgb_col[h_5,:] = np.stack((v[h_5], p[h_5], q[h_5])).T
    return rgb_col

def rgb_to_hsv(rgb_col):
    '''
    rgb_col has to be a 2 axis array with shape [:, 3] or [:, 4] if has alpha
    math taken from https://en.wikipedia.org/wiki/HSL_and_HSV
    '''
    hsv_col = np.zeros(rgb_col.shape)
    max_comp = np.amax(rgb_col[:,:3], axis=1)
    min_comp = np.amin(rgb_col[:,:3], axis=1)
    delta = max_comp - min_comp
    hsv_col[delta == 0, 0] = 0
    mask1 = max_comp == rgb_col[:, 0]
    mask2 = rgb_col[:, 1] >= rgb_col[:, 2]
    mask3 = rgb_col[:, 1] < rgb_col[:, 2]
    mask_g1= mask1 * mask2
    mask_g2= mask1 * mask3
    mask_g3 = max_comp == rgb_col[:, 1]
    mask_g4 = max_comp == rgb_col[:, 2]
    hsv_col[mask_g1, 0] = (rgb_col[mask_g1, 1] - rgb_col[mask_g1, 2])/(delta[mask_g1] * 6)
    hsv_col[mask_g2, 0] = (rgb_col[mask_g2, 1] - rgb_col[mask_g2, 2])/(delta[mask_g2] * 6) + 1
    hsv_col[mask_g3, 0] = (rgb_col[mask_g3, 2] - rgb_col[mask_g3, 0])/(delta[mask_g3] * 6) + 1/3
    hsv_col[mask_g4, 0] = (rgb_col[mask_g4, 0] - rgb_col[mask_g4, 1])/(delta[mask_g4] * 6) + 2/3

    mask_s = max_comp == 0
    mask_other = np.invert(mask_s)
    hsv_col[mask_s, 0] = 0
    hsv_col[mask_s, 1] = 0
    hsv_col[mask_other, 1] = 1 - min_comp[mask_other] / max_comp[mask_other]
    hsv_col[:, 2] = max_comp
    if rgb_col.shape[1] == 4:
        hsv_col[:, 3] = rgb_col[:, 3]
    return hsv_col

def rgb_to_hsl(rgb_col):
    '''
    rgb_col has to be a 2 axis array with shape [:, 3] or [:, 4] if has alpha
    math taken from https://en.wikipedia.org/wiki/HSL_and_HSV
    '''
    hsl_col = np.zeros(rgb_col.shape)
    max_comp = np.amax(rgb_col[:,:3], axis=1)
    min_comp = np.amin(rgb_col[:,:3], axis=1)
    delta = (max_comp - min_comp) * 6
    mask1 = max_comp == rgb_col[:, 0]
    mask2 = rgb_col[:, 1] >= rgb_col[:, 2]
    mask3 = rgb_col[:, 1] < rgb_col[:, 2]
    mask_g1= mask1 * mask2
    mask_g2= mask1 * mask3
    mask_g3 = max_comp == rgb_col[:, 1]
    mask_g4 = max_comp == rgb_col[:, 2]
    hsl_col[mask_g1, 0] = (rgb_col[mask_g1, 1] - rgb_col[mask_g1, 2]) / (delta[mask_g1])
    hsl_col[mask_g2, 0] = (rgb_col[mask_g2, 1] - rgb_col[mask_g2, 2]) / (delta[mask_g2]) + 1
    hsl_col[mask_g3, 0] = (rgb_col[mask_g3, 2] - rgb_col[mask_g3, 0]) / (delta[mask_g3]) + 1/3
    hsl_col[mask_g4, 0] = (rgb_col[mask_g4, 0] - rgb_col[mask_g4, 1]) / (delta[mask_g4]) + 2/3
    hsl_col[delta == 0, 0] = 0

    mask_s = max_comp == 0
    mask_s1 = min_comp == 1
    hsl_col[mask_s,1] = 0
    hsl_col[mask_s1,1] = 0
    mask_other = np.invert((mask_s + mask_s1) > 0)

    hsl_col[mask_other, 1] = (max_comp[mask_other] - min_comp[mask_other])/(1 - np.abs(max_comp[mask_other] + min_comp[mask_other] - 1))
    hsl_col[:, 2] = (max_comp + min_comp)/2
    if rgb_col.shape[1] == 4:
        hsl_col[:, 3] = rgb_col[:, 3]
    return hsl_col
