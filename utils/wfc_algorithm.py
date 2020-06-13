"""
Initial code was taken from Houdini software implementation
https://github.com/sideeffects/SideFXLabs
"""

from itertools import chain

import numpy as np


class WaveFunctionCollapse:
    # wave = WaveFunctionCollapse(*params)  this step will read input image and create patterns
    # new_image = wave.solve(*params)  this step will generate output image

    def __init__(
            self,
            image,
            patter_size=3,
            periodic_input=True,
            rotate_patterns=True):

        self.input_grid_size = image.shape
        self.input_sample_image = image.reshape(-1, 4).tolist()
        self.periodic_input = periodic_input
        self.add_rotations = rotate_patterns
        self.pattern_size = patter_size

        self.output_grid_size = None
        self.seed = None
        self.tile_around_bounds = None

        self.patterns = []
        self.patterns_transforms = []
        self.pattern_frequencies = []
        self.number_of_unique_patterns = None
        self.output_grid = {}
        self.entropy_grid = {}
        self.solve_starting_point_index = None
        self.allowed_pattern_adjacencies = {}
        self.nbr_directions = ((-1, 0), (1, 0), (0, -1), (0, 1))
        self.respect_user_constraints = False
        self.use_input_pattern_frequency = 1

        self.create_patterns_from_input()

    def solve(self,
              output_size=(10, 10),
              seed=0,
              tiling_output=False,
              max_number_contradiction_tries=1):

        self.output_grid_size = output_size
        self.tile_around_bounds = tiling_output

        for solve_attempt in range(max_number_contradiction_tries):

            # Set the seed for our random picking of values
            np.random.seed(seed + solve_attempt * 100)

            # Initialize WFC process
            self.initialize_grid()
            self.initialize_entropy_grid()
            self.calculate_adjacencies()

            if self.respect_user_constraints:
                success = ForceUserConstraints()  # is this need?
            else:
                success = True

            if success:
                # Run the WFC solve itself
                success = self.run_wfc_solve()

            # Assign the output values
            if success:
                return self.assign_wave_to_output()

        # If we have exceeded the number of retries for the solve,
        # we will throw an error to tell the user no solution has been found
        raise RuntimeError("Looks like solution for current input parameters can't be found. "
                           "Try to change seed or number of contradiction tries")

    def create_patterns_from_input(self):
        # Here we will take the input grid, extract its values (name attribute), and cut it up into NxN size patterns
        # Kernel to store data in
        search_kernel = tuple(
            tuple(i + n * self.input_grid_size[0] for i in range(self.pattern_size)) for n in range(self.pattern_size))

        all_temp_patterns = []
        all_temp_patterns_transforms = []

        if self.periodic_input:
            offset = 0
        else:
            offset = (self.pattern_size - 1)

        # Loop over grid
        for y in range(self.input_grid_size[1] - offset):
            for x in range(self.input_grid_size[0] - offset):

                matrix_as_list = []
                for item in search_kernel:
                    tmp = []
                    for sub_items in item:
                        list_index = int(((x + sub_items) % self.input_grid_size[0]) + (
                                        ((item[0] + self.input_grid_size[0] * y) / self.input_grid_size[0])
                                        % self.input_grid_size[1]) * self.input_grid_size[0])
                        tmp.append(self.input_sample_image[list_index])

                    # This is where variations would take place

                    matrix_as_list.append(tuple(tmp))

                temp_pattern = tuple(matrix_as_list)

                if not self.add_rotations:
                    all_temp_patterns.append(temp_pattern)
                    all_temp_patterns_transforms.append([0, 1, 1])
                else:
                    for x in range(4):
                        temp_pattern = list(zip(*temp_pattern[::-1]))
                        all_temp_patterns.append(temp_pattern)
                        all_temp_patterns_transforms.append([(x + 1) * 90, 1, 1])
                        # Maybe add horizontal flip too??
                        # all_temp_patterns.append([a[::-1] for a in temp_pattern]) # Flip X
                        # all_temp_patterns_transforms.append([(x+1)*90, -1, 1])

        all_temp_patterns = [tuple(chain.from_iterable(p)) for p in all_temp_patterns]

        self.patterns = []
        self.patterns_transforms = []
        self.pattern_frequencies = []

        for i, pattern in enumerate(all_temp_patterns):
            if pattern not in self.patterns:
                self.patterns.append(pattern)
                self.pattern_frequencies.append(1)
                self.patterns_transforms.append(all_temp_patterns_transforms[i])
            else:
                index = self.patterns.index(pattern)
                self.pattern_frequencies[index] += 1

        self.number_of_unique_patterns = len(self.pattern_frequencies)

    def initialize_grid(self):
        # Here we create a list that will be used as our output grid. (Used for solving in)

        for x in range(self.output_grid_size[0] * self.output_grid_size[1]):
            self.output_grid[x] = set(range(self.number_of_unique_patterns))

    def initialize_entropy_grid(self):
        # Here we create grid that matches the output grid, but we store entropy values instead.
        # (Entropy = Number of remaining legal patterns)

        for x in range(self.output_grid_size[0] * self.output_grid_size[1]):
            self.entropy_grid[x] = self.number_of_unique_patterns

        # Pick starting point for solve. (Random if not specified)
        if self.solve_starting_point_index is None:
            # solve_starting_point_index = np.random.randint(NumberOfUniquePatterns)
            self.solve_starting_point_index = np.random.randint(len(self.entropy_grid.keys()))

        self.entropy_grid[self.solve_starting_point_index] = self.number_of_unique_patterns - 1

    def calculate_adjacencies(self):
        # If PatternIndex = 10 has been observed to be to the left of of PatternIndex = 15 in the InputGrid:
        # AllowedPatternAdjacencies[PatternIndex=15][0].add(PatternIndex=10)
        # Directions: 0 = left, 1 = right, 2 = up, 3 = down
        # OUTPUT EXAMPLE PatternIndex = 15 --> (LEFT: set([65, 36, 69, 44, 87, 56, 29]),
        # RIGHT: set([8]), UP: set([32, 64, 10, 12, 14, 83, 21]), DOWN: set([15]))

        # Initialize empty AllowedPatternAdjacencies
        for x in range(self.number_of_unique_patterns):
            self.allowed_pattern_adjacencies[x] = tuple(set() for _ in range(len(self.nbr_directions)))

        # Comparing patterns to each other
        for PatternIndex1 in range(self.number_of_unique_patterns):
            for PatternIndex2 in range(self.number_of_unique_patterns):

                pattern1_boundary_columns = [n for i, n in enumerate(self.patterns[PatternIndex1]) if
                                             i % self.pattern_size != (self.pattern_size - 1)]
                pattern2_boundary_columns = [n for i, n in enumerate(self.patterns[PatternIndex2]) if
                                             i % self.pattern_size != 0]

                # Compare Columns compatability
                if pattern1_boundary_columns == pattern2_boundary_columns:
                    self.allowed_pattern_adjacencies[PatternIndex1][0].add(PatternIndex2)
                    self.allowed_pattern_adjacencies[PatternIndex2][1].add(PatternIndex1)

                pattern1_boundary_rows = self.patterns[PatternIndex1][
                                       :(self.pattern_size * self.pattern_size) - self.pattern_size]
                pattern2_boundary_rows = self.patterns[PatternIndex2][self.pattern_size:]

                if pattern1_boundary_rows == pattern2_boundary_rows:
                    self.allowed_pattern_adjacencies[PatternIndex1][2].add(PatternIndex2)
                    self.allowed_pattern_adjacencies[PatternIndex2][3].add(PatternIndex1)

    def run_wfc_solve(self):
        # This runs the actual WFC solve
        running = True
        while running:

            # Find the cell with the lowest entropy value, and assign a random valid PatternIndex
            lowest_entropy_cell = self.get_lowest_entropy_cell()
            pattern_index_for_cell = self.get_random_allowed_pattern_index_from_cell(lowest_entropy_cell)
            self.assign_pattern_to_cell(lowest_entropy_cell, pattern_index_for_cell)

            # Propagate the OutputGrid after collapsing the LowestEntropyCell
            running, error = self.propagate_grid_cells(lowest_entropy_cell)

            # Check if all cells in the OutputGrid have collapsed yet (done solving)
            if len(self.entropy_grid.keys()) == 0:
                running = False

        # Check if we have ran into an error. (contradiction while propagating)
        if error == 1:
            return False
        else:
            return True

    def get_lowest_entropy_cell(self):
        # Find the list entry in the entropy grid with the lowest value
        return min(self.entropy_grid, key=self.entropy_grid.get)

    def get_random_allowed_pattern_index_from_cell(self, cell):
        # Assign a random allowed pattern_index to given cell.
        # This can either use frequency of found patterns as a weighted random or not depending on user parm
        if self.use_input_pattern_frequency == 1:
            return np.random.choice(
                [pattern_index for pattern_index in self.output_grid[cell]
                 for i in range(self.pattern_frequencies[pattern_index])])
        else:
            return np.random.choice([pattern_index for pattern_index in self.output_grid[cell]])

    def assign_pattern_to_cell(self, cell, pattern_index):
        # Assign given cell a chosen PatternIndex, and delete cell from EntropyGrid (Cell has collapsed)
        self.output_grid[cell] = {pattern_index}
        del self.entropy_grid[cell]

    def propagate_grid_cells(self, cell):
        # This propagates all the cells that should have been affected from the just-collapsed cell

        # We are using a stack to add newly found to-be-updated cells to
        to_update_stack = {cell}
        while len(to_update_stack) != 0:
            cell_index = to_update_stack.pop()

            # loop through neighbor cells of currently propagated cell
            for direction, transform in enumerate(self.nbr_directions):

                neighbor_index_is_valid = True

                x = int((cell_index % self.output_grid_size[0] + transform[0]) % self.output_grid_size[0])
                y = int((cell_index / self.output_grid_size[0] + transform[1]) % self.output_grid_size[1])
                neighbor_cell_index = x + y * self.output_grid_size[0]  # index of neighboring cell

                # If the user does not want the WFC solve to create a tiling output,
                # we just state that the found neighbor cell is invalid and don't propagate it
                if not self.tile_around_bounds:
                    x_is_wrapping = abs(neighbor_cell_index % self.output_grid_size[0]
                                        - cell_index % self.output_grid_size[0]) > 1
                    y_is_wrapping = abs(neighbor_cell_index / self.output_grid_size[1]
                                        - cell_index / self.output_grid_size[1]) > 1

                    if x_is_wrapping or y_is_wrapping:
                        neighbor_index_is_valid = False

                # Cell has not yet been collapsed yet
                if neighbor_cell_index in self.entropy_grid and neighbor_index_is_valid:

                    # These are all the allowed patterns for the direction of the checked neighbor cell
                    pattern_indices_in_cell = {n for pattern_index in self.output_grid[cell_index] for n in
                                               self.allowed_pattern_adjacencies[pattern_index][direction]}

                    # These are all the patterns the neighbor allows itself
                    pattern_indices_in_neighbor_cell = self.output_grid[neighbor_cell_index]

                    # Make sure we need to update the cell
                    # by checking if the currently pattern_indices_in_cell patterns for the neighbor cells
                    # are already fully contained in the now reduced set of patterns
                    if not pattern_indices_in_neighbor_cell.issubset(pattern_indices_in_cell):

                        shared_cell_and_neighbor_pattern_indices = set(
                            [x for x in pattern_indices_in_cell if x in pattern_indices_in_neighbor_cell])

                        if len(shared_cell_and_neighbor_pattern_indices) == 0:
                            return False, 1

                        self.output_grid[neighbor_cell_index] = shared_cell_and_neighbor_pattern_indices
                        self.entropy_grid[neighbor_cell_index] = len(self.output_grid[neighbor_cell_index])
                        to_update_stack.add(neighbor_cell_index)

        return True, 0

    def assign_wave_to_output(self):
        # This finds and assigns the picked PatternIndex to the output grid as attributes
        flat_out_image = []
        for x in self.output_grid.keys():
            val = next(iter(self.output_grid[x]))
            flat_out_image.append(self.patterns[val][0])

        out_image = []
        for i_row in range(self.output_grid_size[1]):
            current_row_position = i_row * self.output_grid_size[0]
            pixel_row = flat_out_image[current_row_position: current_row_position + self.output_grid_size[0]]
            out_image.append(pixel_row)

        return out_image


# def ForceUserConstraints():
    # This function handles assigning user constraints based on attached attribute values to the output grid
#     for cellindex, cellvalue in enumerate(UserConstraintAttributes):
#         if cellvalue != \"WFC_Initialize\" and cellvalue in UserConstraintAttributes:
#             AllowedIndices = [x for x in range(len(Patterns)) if cellvalue == Patterns[x][0]]
#             # print len(AllowedIndices)
#
#             PickedIndex = np.random.choice([PatternIndex for PatternIndex in AllowedIndices])
#             assign_pattern_to_cell(cellindex, PickedIndex)
#             Running, Error = propagate_grid_cells(cellindex)
#             if Error == 1:
#                 return False
#
#     return True
