import bpy
import numpy as np


def array_as(a, shape):
    if a.shape == shape:
        return a
    new_a = np.empty(shape, dtype=a.dtype)
    new_a[:len(a)] = a
    new_a[len(a):] = a[-1]
    return new_a


'''from sverchok redux
def assign_BW_image(image, buffer):
    np_buff = np.empty(len(image.pixels), dtype=np.float32)
    np_buff.shape = (-1, 4)
    np_buff[:, :] = buffer[:, np.newaxis]
    np_buff[:, 3] = 1
    np_buff.shape = -1
    image.pixels[:] = np_buff
    return image
'''


def assign_BW_image(image, buffer):
    np_buff = np.empty(len(image.pixels), dtype=np.float32)
    np_buff.shape = (-1, 4)
    np_buff[:, :] = np.array(buffer)[:, np.newaxis]
    np_buff[:, 3] = 1
    np_buff.shape = -1
    image.pixels[:] = np_buff
    return image


def assign_RGB_image(image, width, height, buffer):
    rgb = np.array(buffer)
    rgb_res = rgb.reshape(width * height, 3)
    alpha = np.empty(len(buffer), dtype=np.float32)
    alpha.fill(1)
    print('alpha filled')
    alpha_res = alpha.reshape(width * height, 3)
    print('concatenate rgb > alpha')
    rgba = np.concatenate((rgb_res, alpha_res), axis=1)
    final = rgba[:, 0:4]
    # print(final)
    print('filling pixels from openGl buffer')
    image.pixels = final.flatten()
