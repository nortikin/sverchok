import bpy
import numpy as np


def array_as(a, shape):
    if a.shape == shape:
        return a
    new_a = np.empty(shape, dtype=a.dtype)
    new_a[:len(a)] = a
    new_a[len(a):] = a[-1]
    return new_a


def assign_BW_image(image, buffer):
    # from sverchok redux, modified version
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
    alpha_res = alpha.reshape(width * height, 3)
    rgba = np.concatenate((rgb_res, alpha_res), axis=1)
    final = rgba[:, 0:4]
    image.pixels = final.flatten()


def get_extension(img_format):
    if img_format in format_mapping:
        extension = '.' + format_mapping.get(img_format, img_format.lower())
    else:
        extension = '.' + img_format.lower()
    return extension


def pass_buffer_to_image(color_mode, img, buf, width, height):
    print('width is: {0}'.format(width))
    print('length img pixels: {0}'.format(len(img.pixels)))
    # print("passing data from buf to pixels ", self.color_mode)
    if color_mode == 'BW':
        assign_BW_image(img, buf)
    elif color_mode == 'RGB':
        assign_RGB_image(img, width, height, buf)
    elif color_mode == 'RGBA':
        img.pixels[:] = buf
