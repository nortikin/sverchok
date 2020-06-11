"Extract patterns from grids of tiles."

from collections import Counter
import numpy as np

from .wfc_utilities import hash_downto


def unique_patterns_2d(agrid, ksize, periodic_input):
    """
    Split tiles array into patches, patch is array of tiles usually size of 2x2 or 3x3
    :param agrid: image with tile IDs instead of colors
    :param ksize: size of the patterns; usually 2 or 3 because bigger gets slower
    :param periodic_input: True -> the input wraps at the edges
    :return: tuple of:
    ids: image patches array where each patch is set by index (0 - inf)
    up: array of unique patches, each patch is array of tiles with size of pattern_width
    patch_codes: image array of parches, each patch is represented by ID
    """
    assert ksize >= 1

    if periodic_input:
        agrid = np.pad(agrid, ((0, ksize - 1), (0, ksize - 1), *(((0, 0), )*(len(agrid.shape) - 2))), mode='wrap')
    else:
        # TODO: implement non-wrapped image handling
        agrid = np.pad(agrid, ((0, ksize - 1), (0, ksize - 1), *(((0, 0), )*(len(agrid.shape) - 2))), mode='wrap')

    patches = np.lib.stride_tricks.as_strided(
        agrid,
        (agrid.shape[0] - ksize + 1, agrid.shape[1] - ksize + 1, ksize, ksize, *agrid.shape[2:]),
        agrid.strides[:2] + agrid.strides[:2] + agrid.strides[2:],
        writeable=False)

    patch_codes = hash_downto(patches, 2)
    uc, ui = np.unique(patch_codes, return_index=True)
    locs = np.unravel_index(ui, patch_codes.shape)
    up = patches[locs[0], locs[1]]
    ids = np.vectorize({code: ind for ind, code in enumerate(uc)}.get)(patch_codes)
    return ids, up, patch_codes


def make_pattern_catalog(tile_grid, pattern_width, input_is_periodic=True):
    """
    Returns a pattern catalog (dictionary of pattern hashes to consituent tiles),
    an ordered list of pattern weights, and an ordered list of pattern contents.
    :param tile_grid: image with tile IDs instead of colors
    :param pattern_width: size of the patterns; usually 2 or 3 because bigger gets slower
    :param input_is_periodic: rue -> the input wraps at the edges
    :return: tuple of:
    dict_of_pattern_contents: ID of a pattern: pattern, pattern usually 2x2 or 3x3 array of tile IDs
    pattern_frequency: ID of a pattern: frequency (int)
    hash_downto_pattern_contents_list: array of unique pattern IDs
    patch_codes: image array of parches, each patch is represented by ID
    """
    _, pattern_contents_list, patch_codes = unique_patterns_2d(tile_grid, pattern_width, input_is_periodic)
    dict_of_pattern_contents = {}
    for pat_idx in range(pattern_contents_list.shape[0]):
        p_hash = hash_downto(pattern_contents_list[pat_idx], 0)
        dict_of_pattern_contents.update({np.asscalar(p_hash): pattern_contents_list[pat_idx]})
    pattern_frequency = Counter(hash_downto(pattern_contents_list, 1))
    return dict_of_pattern_contents, pattern_frequency, hash_downto(pattern_contents_list, 1), patch_codes


def identity_grid(grid):
    "do nothing to the grid"
    return grid


def reflect_grid(grid):
    "reflect the grid left/right"
    return np.fliplr(grid)


def rotate_grid(grid):
    "rotate the grid"
    return np.rot90(grid, axes=(1,0))


def make_pattern_catalog_with_rotations(tile_grid, pattern_width, rotations=7, input_is_periodic=True):
    """
    Split tile array into patches with their rotations
    :param tile_grid: image with tile IDs instead of colors
    :param pattern_width: size of the patterns; usually 2 or 3 because bigger gets slower
    :param rotations: how many reflections and/or rotations to use with the patterns
    :param input_is_periodic: True -> the input wraps at the edges
    :return: tuple of:
    merged_dict_of_pattern_contents: map of pattern ID and pattern, pattern is usually 2x2 or 3x3 array of tile IDs
    merged_pattern_frequency: map of patter ID and its frequency (int)
    merged_pattern_contents_list: array of unique pattern IDs
    merged_patch_codes: image array of pattern IDs
    """
    rotated_tile_grid = tile_grid.copy()
    merged_dict_of_pattern_contents = {}
    merged_pattern_frequency = Counter()
    merged_pattern_contents_list = None
    merged_patch_codes = None

    def _make_catalog():
        nonlocal rotated_tile_grid, merged_dict_of_pattern_contents, merged_pattern_contents_list, merged_pattern_frequency, merged_patch_codes
        dict_of_pattern_contents, pattern_frequency, pattern_contents_list, patch_codes = make_pattern_catalog(rotated_tile_grid, pattern_width, input_is_periodic)
        merged_dict_of_pattern_contents.update(dict_of_pattern_contents)
        merged_pattern_frequency.update(pattern_frequency)
        if merged_pattern_contents_list is None:
            merged_pattern_contents_list = pattern_contents_list.copy()
        else:
            merged_pattern_contents_list = np.unique(np.concatenate((merged_pattern_contents_list, pattern_contents_list)))
        if merged_patch_codes is None:
            merged_patch_codes = patch_codes.copy()

    counter = 0
    grid_ops = [identity_grid, reflect_grid, rotate_grid, reflect_grid, rotate_grid, reflect_grid, rotate_grid, reflect_grid]
    while counter <= (rotations):
        rotated_tile_grid = grid_ops[counter](rotated_tile_grid.copy())
        _make_catalog()
        counter += 1

    return merged_dict_of_pattern_contents, merged_pattern_frequency, merged_pattern_contents_list, merged_patch_codes


def pattern_grid_to_tiles(pattern_grid, pattern_catalog):
    anchor_x = 0
    anchor_y = 0

    def pattern_to_tile(pattern):
        return pattern_catalog[pattern][anchor_x][anchor_y]

    return np.vectorize(pattern_to_tile)(pattern_grid)
