"Extract patterns from grids of tiles."

from collections import Counter
import numpy as np

from .wfc_utilities import hash_downto


def unique_patterns_2d(agrid, ksize, periodic_input):
    assert ksize >= 1
    if periodic_input:
        agrid = np.pad(agrid, ((0, ksize - 1), (0, ksize - 1), *(((0, 0), )*(len(agrid.shape) - 2))), mode='wrap')
    else:
        # TODO: implement non-wrapped image handling
        #a = np.pad(a, ((0,k-1),(0,k-1),*(((0,0),)*(len(a.shape)-2))), mode='constant', constant_values=None)
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


def unique_patterns_brute_force(grid, size, periodic_input):
    padded_grid = np.pad(grid, ((0,size-1),(0,size-1),*(((0,0),)*(len(grid.shape)-2))), mode='wrap')
    patches = []
    for x in range(grid.shape[0]):
        row_patches = []
        for y in range(grid.shape[1]):
            row_patches.append(np.ndarray.tolist(padded_grid[x:x+size, y:y+size]))
        patches.append(row_patches)
    patches = np.array(patches)
    patch_codes = hash_downto(patches,2)
    uc, ui = np.unique(patch_codes, return_index=True)
    locs = np.unravel_index(ui, patch_codes.shape)
    up = patches[locs[0],locs[1]]
    ids = np.vectorize({c: i for i,c in enumerate(uc)}.get)(patch_codes)
    return ids, up


def make_pattern_catalog(tile_grid, pattern_width, input_is_periodic=True):
    """Returns a pattern catalog (dictionary of pattern hashes to consituent tiles), 
an ordered list of pattern weights, and an ordered list of pattern contents."""
    patterns_in_grid, pattern_contents_list, patch_codes = unique_patterns_2d(tile_grid, pattern_width, input_is_periodic)
    dict_of_pattern_contents = {}
    for pat_idx in range(pattern_contents_list.shape[0]):
        p_hash = hash_downto(pattern_contents_list[pat_idx], 0)
        dict_of_pattern_contents.update({np.asscalar(p_hash) : pattern_contents_list[pat_idx]})
    pattern_frequency = Counter(hash_downto(pattern_contents_list, 1))
    return dict_of_pattern_contents, pattern_frequency, hash_downto(pattern_contents_list, 1), patch_codes


def identity_grid(grid):
    "do nothing to the grid"
    #return np.array([[7,5,5,5],[5,0,0,0],[5,0,1,0],[5,0,0,0]])
    return grid


def reflect_grid(grid):
    "reflect the grid left/right"
    return np.fliplr(grid)


def rotate_grid(grid):
    "rotate the grid"
    return np.rot90(grid, axes=(1,0))


def make_pattern_catalog_with_rotations(tile_grid, pattern_width, rotations=7, input_is_periodic=True):
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
        #print(rotated_tile_grid.shape)
        #print(np.array_equiv(reflect_grid(rotated_tile_grid.copy()), rotate_grid(rotated_tile_grid.copy())))

        #print(counter)
        #print(grid_ops[counter].__name__)
        rotated_tile_grid = grid_ops[counter](rotated_tile_grid.copy())
        #print(rotated_tile_grid)
        #print("---")
        _make_catalog()
        counter += 1

    #assert False
    return merged_dict_of_pattern_contents, merged_pattern_frequency, merged_pattern_contents_list, merged_patch_codes


def pattern_grid_to_tiles(pattern_grid, pattern_catalog):
    anchor_x = 0
    anchor_y = 0
    def pattern_to_tile(pattern):
        # if isinstance(pattern, list):
        #     ptrns = []
        #     for p in pattern:
        #         print(p)
        #         ptrns.push(pattern_to_tile(p))
        #     print(ptrns)
        #     assert False
        #     return ptrns
        return pattern_catalog[pattern][anchor_x][anchor_y]
    return np.vectorize(pattern_to_tile)(pattern_grid)
