# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

import random
import math
from enum import Enum

import numpy as np

import bpy

from sverchok.node_tree import SverchCustomTreeNode
from sverchok.data_structure import updateNode
from sverchok.utils.wfc_algorithm import WaveFunctionCollapse


X, Y = 0, 1

# in [[v1, v2],
#     [v3, v4]] first index will shift by Y direction second by X
UP = (1, 0)
LEFT = (0, -1)
DOWN = (-1, 0)
RIGHT = (0, 1)


class Directions(Enum):
    UP = 1
    RIGHT = 2
    DOWN = 3
    LEFT = 4

    def get_other(self, array, current_co):
        if self == Directions.UP:
            return array[current_co[Y] - 1][current_co[X]]
        elif self == Directions.RIGHT:
            return array[current_co[Y]][current_co[X] + 1]
        elif self == Directions.DOWN:
            return array[current_co[Y] + 1][current_co[X]]
        elif self == Directions.LEFT:
            return array[current_co[Y]][current_co[X] - 1]

    def get_other_co(self, current_co):
        if self == Directions.UP:
            return current_co[X], current_co[Y] - 1
        elif self == Directions.RIGHT:
            return current_co[X] + 1, current_co[Y]
        elif self == Directions.DOWN:
            return current_co[X], current_co[Y] + 1
        elif self == Directions.LEFT:
            return current_co[X] - 1, current_co[Y]


class CompatibilityOracle(object):
    """The CompatibilityOracle class is responsible for telling us
    which combinations of tiles and directions are compatible. It's
    so simple that it perhaps doesn't need to be a class, but I think
    it helps keep things clear.
    """

    def __init__(self, data):
        self.data = data

    def check(self, tile1, tile2, direction):
        return (tile1, tile2, direction) in self.data

    def __repr__(self):
        return f"<Oracle {self.data}>"


class Wavefunction(object):
    """The Wavefunction class is responsible for storing which tiles
    are permitted and forbidden in each location of an output image.
    """

    @staticmethod
    def mk(size, weights):
        """Initialize a new Wavefunction for a grid of `size`,
        where the different tiles have overall weights `weights`.

        Arguments:
        size -- a 2-tuple of (width, height)
        weights -- a dict of tile -> weight of tile
        """
        coefficients = Wavefunction.init_coefficients(size, weights.keys())
        return Wavefunction(coefficients, weights)

    @staticmethod
    def init_coefficients(size, tiles):
        """Initializes a 2-D wavefunction matrix of coefficients.
        The matrix has size `size`, and each element of the matrix
        starts with all tiles as possible. No tile is forbidden yet.

        NOTE: coefficients is a slight misnomer, since they are a
        set of possible tiles instead of a tile -> number/bool dict. This
        makes the code a little simpler. We keep the name `coefficients`
        for consistency with other descriptions of Wavefunction Collapse.

        Arguments:
        size -- a 2-tuple of (width, height)
        tiles -- a set of all the possible tiles

        Returns:
        A 2-D matrix in which each element is a set
        """
        coefficients = []

        for y in range(size[0]):
            row = []
            for x in range(size[1]):
                row.append(set(tiles))
            coefficients.append(row)

        return coefficients

    def __init__(self, coefficients, weights):
        self.coefficients = coefficients
        self.weights = weights

    def get(self, co_ords):
        """Returns the set of possible tiles at `co_ords`"""
        return self.coefficients[co_ords[Y]][co_ords[X]]

    def get_collapsed(self, co_ords):
        """Returns the only remaining possible tile at `co_ords`.
        If there is not exactly 1 remaining possible tile then
        this method raises an exception.
        """
        opts = self.get(co_ords)
        assert (len(opts) == 1)
        return next(iter(opts))

    def get_all_collapsed(self):
        """Returns a 2-D matrix of the only remaining possible
        tiles at each location in the wavefunction. If any location
        does not have exactly 1 remaining possible tile then
        this method raises an exception.
        """
        y_length = len(self.coefficients)
        x_length = len(self.coefficients[0])

        collapsed = []
        for y in range(y_length):
            row = []
            for x in range(x_length):
                row.append(self.get_collapsed((x, y)))
            collapsed.append(row)

        return collapsed

    def shannon_entropy(self, co_ords):
        """Calculates the Shannon Entropy of the wavefunction at
        `co_ords`.
        """
        x, y = co_ords

        sum_of_weights = 0
        sum_of_weight_log_weights = 0
        for tile in self.coefficients[y][x]:
            weight = self.weights[tile]
            sum_of_weights += weight
            sum_of_weight_log_weights += weight * math.log(weight)

        return math.log(sum_of_weights) - (sum_of_weight_log_weights / sum_of_weights)

    def is_fully_collapsed(self):
        """Returns true if every element in Wavefunction is fully
        collapsed, and false otherwise.
        """
        for y, row in enumerate(self.coefficients):
            for x, tiles in enumerate(row):
                if len(tiles) > 1:
                    return False

        return True

    def collapse(self, co_ords):
        """Collapses the wavefunction at `co_ords` to a single, definite
        tile. The tile is chosen randomly from the remaining possible tiles
        at `co_ords`, weighted according to the Wavefunction's global
        `weights`.

        This method mutates the Wavefunction, and does not return anything.
        """
        tiles = self.coefficients[co_ords[Y]][co_ords[X]]
        valid_weights = {tile: weight for tile, weight in self.weights.items() if tile in tiles}

        total_weights = sum(valid_weights.values())
        rnd = random.random() * total_weights

        chosen = None
        for tile, weight in valid_weights.items():
            rnd -= weight
            if rnd < 0:
                chosen = tile
                break

        self.coefficients[co_ords[Y]][co_ords[X]] = {chosen}

    def constrain(self, co_ords, forbidden_tile):
        """Removes `forbidden_tile` from the list of possible tiles
        at `co_ords`.

        This method mutates the Wavefunction, and does not return anything.
        """
        self.coefficients[co_ords[Y]][co_ords[X]].remove(forbidden_tile)

    def __repr__(self):
        return f"<Wave: {self.coefficients}>"


class Model(object):
    """The Model class is responsible for orchestrating the
    Wavefunction Collapse algorithm.
    """

    def __init__(self, output_size, weights, compatibility_oracle):
        self.output_size = output_size
        self.compatibility_oracle = compatibility_oracle

        self.wavefunction = Wavefunction.mk(output_size, weights)

    def run(self):
        """Collapses the Wavefunction until it is fully collapsed,
        then returns a 2-D matrix of the final, collapsed state.
        """
        while not self.wavefunction.is_fully_collapsed():
            self.iterate()

        return self.wavefunction.get_all_collapsed()

    def iterate(self):
        """Performs a single iteration of the Wavefunction Collapse
        Algorithm.
        """
        # 1. Find the co-ordinates of minimum entropy
        co_ords = self.min_entropy_co_ords()
        # 2. Collapse the wavefunction at these co-ordinates
        self.wavefunction.collapse(co_ords)
        # 3. Propagate the consequences of this collapse
        self.propagate(co_ords)

    def propagate(self, co_ords):
        """Propagates the consequences of the wavefunction at `co_ords`
        collapsing. If the wavefunction at (x,y) collapses to a fixed tile,
        then some tiles may not longer be theoretically possible at
        surrounding locations.

        This method keeps propagating the consequences of the consequences,
        and so on until no consequences remain.
        """
        stack = [co_ords]

        while len(stack) > 0:
            cur_coords = stack.pop()
            # Get the set of all possible tiles at the current location
            cur_possible_tiles = self.wavefunction.get(cur_coords).copy()

            # Iterate through each location immediately adjacent to the
            # current location.
            for direction in valid_dirs(cur_coords, self.output_size):
                other_co = direction.get_other_co(cur_coords)
                # Iterate through each possible tile in the adjacent location's wavefunction.
                for other_tile in direction.get_other(self.wavefunction.coefficients, cur_coords).copy():
                    # Check whether the tile is compatible with any tile in
                    # the current location's wavefunction.
                    other_tile_is_possible = any([
                        self.compatibility_oracle.check(cur_tile, other_tile, direction) for cur_tile in cur_possible_tiles
                    ])
                    # If the tile is not compatible with any of the tiles in
                    # the current location's wavefunction then it is impossible
                    # for it to ever get chosen. We therefore remove it from
                    # the other location's wavefunction.
                    if not other_tile_is_possible:
                        self.wavefunction.constrain(other_co, other_tile)
                        stack.append(other_co)

    def min_entropy_co_ords(self):
        """Returns the co-ords of the location whose wavefunction has
        the lowest entropy.
        """
        min_entropy = None
        min_entropy_coords = None

        for y, row in enumerate(self.wavefunction.coefficients):
            for x, tiles in enumerate(row):
                if len(tiles) == 1:
                    continue

                entropy = self.wavefunction.shannon_entropy((x, y))
                # Add some noise to mix things up a little
                entropy_plus_noise = entropy - (random.random() / 1000)
                if min_entropy is None or entropy_plus_noise < min_entropy:
                    min_entropy = entropy_plus_noise
                    min_entropy_coords = (x, y)

        return min_entropy_coords


def valid_dirs(cur_co, matrix_shape):
    """Returns the valid directions from `cur_co_ord` in a matrix
    of `matrix_size`. Ensures that we don't try to take step to the
    left when we are already on the left edge of the matrix.
    """
    y_length, x_length = matrix_shape[:2]
    dirs = []

    if cur_co[X] > 0:
        dirs.append(Directions.LEFT)
    if cur_co[X] < x_length - 1:
        dirs.append(Directions.RIGHT)
    if cur_co[Y] > 0:
        dirs.append(Directions.UP)
    if cur_co[Y] < y_length - 1:
        dirs.append(Directions.DOWN)

    return dirs


def parse_example_matrix(matrix: np.ndarray):
    """Parses an example `matrix`. Extracts:

    1. Tile compatibilities - which pairs of tiles can be placed next
        to each other and in which directions
    2. Tile weights - how common different tiles are

    Arguments:
    matrix -- a 2-D matrix of tiles

    Returns:
    A tuple of:
    * A set of compatibile tile combinations, where each combination is of
        the form (tile1, tile2, direction)
    * A dict of weights of the form tile -> weight
    """
    compatibilities = set()
    weights = dict()
    for y, row in enumerate(matrix):
        for x, cur_tile in enumerate(row):
            cur_tile = tuple(cur_tile)
            if cur_tile not in weights:
                weights[cur_tile] = 0
            weights[cur_tile] += 1

            for direction in valid_dirs((x, y), matrix.shape):
                other_tile = tuple(direction.get_other(matrix, (x, y)))
                compatibilities.add((cur_tile, other_tile, direction))
    return compatibilities, weights


def load_image(image_name) -> np.ndarray:
    image = bpy.data.images[image_name]
    width, height = image.size
    pixels = np.array(image.pixels).reshape((height, width, 4))
    return pixels


class SvWFCTextureNode(bpy.types.Node, SverchCustomTreeNode):
    """
    Triggers: image

    ...
    ...
    """
    bl_idname = 'SvWFCTextureNode'
    bl_label = 'WFC Texture'
    bl_icon = 'AUTOMERGE_ON'

    image_name: bpy.props.StringProperty(name="Image", default="", update=updateNode)
    height: bpy.props.IntProperty(default=10, update=updateNode)
    width: bpy.props.IntProperty(default=10, update=updateNode)
    seed: bpy.props.IntProperty(update=updateNode)
    pattern_size: bpy.props.IntProperty(default=3, min=1, max=5, update=updateNode)
    rotate_patterns: bpy.props.BoolProperty(update=updateNode)
    tiling_output: bpy.props.BoolProperty(update=updateNode)
    periodic_input: bpy.props.BoolProperty(default=True, update=updateNode)

    def sv_init(self, context):
        self.inputs.new("SvStringsSocket", "height").prop_name = 'height'
        self.inputs.new("SvStringsSocket", "width").prop_name = 'width'
        self.inputs.new("SvStringsSocket", "seed").prop_name = 'seed'
        self.inputs.new("SvStringsSocket", "pattern size").prop_name = 'pattern_size'
        self.outputs.new("SvColorSocket", "image")

    def draw_buttons(self, context, layout):
        layout.prop_search(self, 'image_name', bpy.data, 'images', text='', icon='IMAGE')
        layout.prop(self, 'rotate_patterns')
        layout.prop(self, 'periodic_input')
        layout.prop(self, 'tiling_output')

    def process(self):
        if not self.image_name:
            return

        image = load_image(self.image_name)
        wave = WaveFunctionCollapse(
            image,
            patter_size=self.pattern_size,
            periodic_input=self.periodic_input,
            rotate_patterns=self.rotate_patterns)

        output = wave.solve(
            output_size=(self.width, self.height),
            seed=self.seed,
            tiling_output=self.tiling_output,
            max_number_contradiction_tries=1)

        self.outputs['image'].sv_set(output)


def register():
    bpy.utils.register_class(SvWFCTextureNode)


def unregister():
    bpy.utils.unregister_class(SvWFCTextureNode)
