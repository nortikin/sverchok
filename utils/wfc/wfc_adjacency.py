"""Convert input data to adjacency information"""

import numpy as np


def adjacency_extraction(pattern_catalog, direction_offsets, pattern_size=(2, 2)):
    """
    Takes a pattern grid and returns a list of all of the legal adjacencies found in it.
    :param pattern_catalog: map of pattern ID and pattern, pattern is usually 2x2 or 3x3 array of tile IDs
    :param direction_offsets: list of indexed and directions
    :param pattern_size: size of the patterns; usually 2 or 3 because bigger gets slower
    :return: list of tuple of direction, pattern ID 1, pattern ID 2
    """

    def is_valid_overlap_xy(adjacency_direction, pattern_1, pattern_2):
        """Given a direction and two patterns, find the overlap of the two patterns 
        and return True if the intersection matches."""
        dimensions = (1,0)
        not_a_number = -1

        # TODO: can probably speed this up by using the right slices, rather than rolling the whole pattern...
        shifted = np.roll(np.pad(pattern_catalog[pattern_2], max(pattern_size), mode='constant', constant_values = not_a_number), adjacency_direction, dimensions)
        compare = shifted[pattern_size[0] : pattern_size[0] + pattern_size[0], pattern_size[1] : pattern_size[1] + pattern_size[1]]

        left = max(0, 0, + adjacency_direction[0])
        right = min(pattern_size[0], pattern_size[0] + adjacency_direction[0])
        top = max(0, 0 + adjacency_direction[1])
        bottom = min(pattern_size[1], pattern_size[1] + adjacency_direction[1])
        a = pattern_catalog[pattern_1][top:bottom, left:right]
        b = compare[top:bottom, left:right]
        res = np.array_equal(a, b)
        return res

    pattern_list = list(pattern_catalog.keys())
    legal = []
    for pattern_1 in pattern_list:
        for pattern_2 in pattern_list:
            for direction_index, direction in direction_offsets:
                if is_valid_overlap_xy(direction, pattern_1, pattern_2):
                    legal.append((direction, pattern_1, pattern_2))

    return legal
