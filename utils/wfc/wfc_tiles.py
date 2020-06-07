"""Breaks an image into consituant tiles."""
import numpy as np

from .wfc_utilities import hash_downto


def image_to_tiles(img, tile_size):
    """
    Takes an images, divides it into tiles, return an array of tiles.
    """
    padding_argument = [(0, 0), (0, 0),(0, 0)]
    for input_dim in [0, 1]:
        padding_argument[input_dim] = (0, (tile_size - img.shape[input_dim]) % tile_size)
    img = np.pad(img, padding_argument, mode='constant')
    tiles = img.reshape((img.shape[0]//tile_size, 
                       tile_size,
                       img.shape[1]//tile_size,
                       tile_size,
                       img.shape[2]
                      )).swapaxes(1, 2)
    return tiles


def make_tile_catalog(image_data, tile_size):
    """
    Takes an image and tile size and returns the following:
    tile_catalog is a dictionary tiles, with the hashed ID as the key
    tile_grid is the original image, expressed in terms of hashed tile IDs
    code_list is the original image, expressed in terms of hashed tile IDs and reduced to one dimension
    unique_tiles is the set of tiles, plus the frequency of occurance
    """
    channels = image_data.shape[2] # Number of color channels in the image
    tiles = image_to_tiles(image_data, tile_size)
    tile_list = np.array(tiles, dtype=np.int64).reshape((tiles.shape[0] * tiles.shape[1], tile_size, tile_size, channels))
    code_list = np.array(hash_downto(tiles, 2), dtype=np.int64).reshape((tiles.shape[0] * tiles.shape[1]))
    tile_grid = np.array(hash_downto(tiles, 2), dtype=np.int64)
    unique_tiles = np.unique(tile_grid, return_counts=True)
    
    tile_catalog = {}
    for i, j in enumerate(code_list):
        tile_catalog[j] = tile_list[i]
    return tile_catalog, tile_grid, code_list, unique_tiles


def tiles_to_images(tile_grid, tile_catalog):
    return
