from itertools import chain

import numpy as np


# User Params
Seed = 0
N = 2  # PatternSearchSize
MaxNumberContradictionTries = 1
UseInputPatternFrequency = 1
TileAroundBounds = True
PeriodicInput = False
respect_user_constraints = False
AddRotations = False
InputGridSize = (3, 3)
OutputGridSize = (10, 10)
SolveStartingPointIndex = None

# Internal Parms
PatternFrequencies = None
Patterns = None
PatternsTransforms = None  # [\"rot\", \"flipX\", \"flipY\"]
NumberOfUniquePatterns = None
NbrDirections = ((-1, 0), (1, 0), (0, -1), (0, 1))
OutputGrid = {}
EntropyGrid = {}
AllowedPatternAdjacencies = {}
InputSampleAttributes = []
UserConstraintAttributes = []


# Here we will take the input grid, extract its values (name attribute), and cut it up into NxN size patterns
def create_patterns_from_input():
    global PatternFrequencies, Patterns, PatternsTransforms, NumberOfUniquePatterns

    # Kernel to store data in
    SearchKernel = tuple(tuple(i + n * InputGridSize[0] for i in range(N)) for n in range(N))

    AllTempPatterns = []
    AllTempPatternsTransforms = []

    if PeriodicInput:
        Offset = 0
    else:
        Offset = (N - 1)

    # Loop over grid
    for y in range(InputGridSize[1] - Offset):
        for x in range(InputGridSize[0] - Offset):

            MatrixAsList = []
            for item in SearchKernel:
                Tmp = []
                for subitems in item:
                    listindex = int(((x + subitems) % InputGridSize[0]) + (
                                ((item[0] + InputGridSize[0] * y) / InputGridSize[0]) % InputGridSize[1]) *
                                InputGridSize[0])
                    Tmp.append(InputSampleAttributes[listindex])

                # This is where variations would take place

                MatrixAsList.append(tuple(Tmp))

            TempPattern = tuple(MatrixAsList)

            if not AddRotations:
                AllTempPatterns.append(TempPattern)
                AllTempPatternsTransforms.append([0, 1, 1])
            else:
                for x in range(4):
                    TempPattern = list(zip(*TempPattern[::-1]))
                    AllTempPatterns.append(TempPattern)
                    AllTempPatternsTransforms.append([(x + 1) * 90, 1, 1])
                    # Maybe add horizontal flip too??
                    # AllTempPatterns.append([a[::-1] for a in TempPattern]) # Flip X
                    # AllTempPatternsTransforms.append([(x+1)*90, -1, 1])

    AllTempPatterns = [tuple(chain.from_iterable(p)) for p in AllTempPatterns]

    Patterns = []
    PatternsTransforms = []
    PatternFrequencies = []

    for i, pattern in enumerate(AllTempPatterns):
        if pattern not in Patterns:
            Patterns.append(pattern)
            PatternFrequencies.append(1)
            PatternsTransforms.append(AllTempPatternsTransforms[i])
        else:
            index = Patterns.index(pattern)
            PatternFrequencies[index] += 1

    NumberOfUniquePatterns = len(PatternFrequencies)
    # print NumberOfUniquePatterns


# Here we create a list that will be used as our output grid. (Used for solving in)
def initialize_grid():
    global OutputGrid

    for x in range(OutputGridSize[0] * OutputGridSize[1]):
        OutputGrid[x] = set(range(NumberOfUniquePatterns))


def initialize_entropy_grid():
    # Here we create grid that matches the output grid, but we store entropy values instead. 
    # (Entropy = Number of remaining legal patterns)
    global EntropyGrid, SolveStartingPointIndex

    for x in range(OutputGridSize[0] * OutputGridSize[1]):
        EntropyGrid[x] = NumberOfUniquePatterns

    # Pick starting point for solve. (Random if not specified)
    if SolveStartingPointIndex is None:
        # SolveStartingPointIndex = np.random.randint(NumberOfUniquePatterns)
        #### LOOK HERE
        SolveStartingPointIndex = np.random.randint(len(EntropyGrid.keys()))

    EntropyGrid[SolveStartingPointIndex] = NumberOfUniquePatterns - 1


def calculate_adjacencies():
    global AllowedPatternAdjacencies

    # If PatternIndex = 10 has been observed to be to the left of of PatternIndex = 15 in the InputGrid:
    # AllowedPatternAdjacencies[PatternIndex=15][0].add(PatternIndex=10)
    # Directions: 0 = left, 1 = right, 2 = up, 3 = down
    # OUTPUT EXAMPLE PatternIndex = 15 --> (LEFT: set([65, 36, 69, 44, 87, 56, 29]), RIGHT: set([8]), UP: set([32, 64, 10, 12, 14, 83, 21]), DOWN: set([15]))

    # Initialize empty AllowedPatternAdjacencies
    for x in range(NumberOfUniquePatterns):
        AllowedPatternAdjacencies[x] = tuple(set() for _ in range(len(NbrDirections)))

    # Comparing patterns to each other
    for PatternIndex1 in range(NumberOfUniquePatterns):
        for PatternIndex2 in range(NumberOfUniquePatterns):

            Pattern1BoundaryColumns = [n for i, n in enumerate(Patterns[PatternIndex1]) if i % N != (N - 1)]
            Pattern2BoundaryColumns = [n for i, n in enumerate(Patterns[PatternIndex2]) if i % N != 0]

            # Compare Columns compatability
            if Pattern1BoundaryColumns == Pattern2BoundaryColumns:
                AllowedPatternAdjacencies[PatternIndex1][0].add(PatternIndex2)
                AllowedPatternAdjacencies[PatternIndex2][1].add(PatternIndex1)

            Pattern1BoundaryRows = Patterns[PatternIndex1][:(N * N) - N]
            Pattern2BoundaryRows = Patterns[PatternIndex2][N:]

            if Pattern1BoundaryRows == Pattern2BoundaryRows:
                AllowedPatternAdjacencies[PatternIndex1][2].add(PatternIndex2)
                AllowedPatternAdjacencies[PatternIndex2][3].add(PatternIndex1)


def get_lowest_entropy_cell():
    # Find the list entry in the entropy grid with the lowest value
    return min(EntropyGrid, key=EntropyGrid.get)


def get_random_allowed_patternIndex_from_cell(cell):
    # Assign a random allowed PatternIndex to given cell. 
    # This can either use frequency of found patterns as a weighted random or not depending on user parm
    if UseInputPatternFrequency == 1:
        return np.random.choice(
            [PatternIndex for PatternIndex in OutputGrid[cell] for i in range(PatternFrequencies[PatternIndex])])
    else:
        return np.random.choice([PatternIndex for PatternIndex in OutputGrid[cell]])


def assign_pattern_to_cell(cell, pattern_index):
    # Assign given cell a chosen PatternIndex, and delete cell from EntropyGrid (Cell has collapsed)
    global OutputGrid, EntropyGrid
    OutputGrid[cell] = {pattern_index}
    del EntropyGrid[cell]


def propagate_grid_cells(cell):
    # This propagates all the cells that should have been affected from the just-collapsed cell
    global EntropyGrid, OutputGrid

    # We are using a stack to add newly found to-be-updated cells to
    ToUpdateStack = {cell}
    while len(ToUpdateStack) != 0:
        CellIndex = ToUpdateStack.pop()

        # loop through neighbor cells of currently propagated cell
        for direction, transform in enumerate(NbrDirections):

            NeighborIndexIsValid = True

            x = int((CellIndex % OutputGridSize[0] + transform[0]) % OutputGridSize[0])
            y = int((CellIndex / OutputGridSize[0] + transform[1]) % OutputGridSize[1])
            NeighborCellIndex = x + y * OutputGridSize[0]  # index of neighboring cell

            # If the user does not want the WFC solve to create a tiling output,
            # we just state that the found neighbor cell is invalid and don't propagate it
            if not TileAroundBounds:
                xiswrapping = abs(NeighborCellIndex % OutputGridSize[0] - CellIndex % OutputGridSize[0]) > 1
                yiswrapping = abs(NeighborCellIndex / OutputGridSize[1] - CellIndex / OutputGridSize[1]) > 1

                if xiswrapping or yiswrapping:
                    NeighborIndexIsValid = False

            # Cell has not yet been collapsed yet
            if NeighborCellIndex in EntropyGrid and NeighborIndexIsValid:

                # These are all the allowed patterns for the direction of the checked neighbor cell
                PatternIndicesInCell = {n for PatternIndex in OutputGrid[CellIndex] for n in
                                        AllowedPatternAdjacencies[PatternIndex][direction]}

                # These are all the patterns the neighbor allows itself
                PatternIndicesInNeighborCell = OutputGrid[NeighborCellIndex]

                # Make sure we need to update the cell
                # by checking if the currently PatternIndicesInCell patterns for the neighbor cells
                # are already fully contained in the now reduced set of patterns
                if not PatternIndicesInNeighborCell.issubset(PatternIndicesInCell):

                    SharedCellAndNeighborPatternIndices = set(
                        [x for x in PatternIndicesInCell if x in PatternIndicesInNeighborCell])

                    if len(SharedCellAndNeighborPatternIndices) == 0:
                        return False, 1

                    OutputGrid[NeighborCellIndex] = SharedCellAndNeighborPatternIndices
                    EntropyGrid[NeighborCellIndex] = len(OutputGrid[NeighborCellIndex])
                    ToUpdateStack.add(NeighborCellIndex)

    return True, 0


# This is a utility function that chops a given list into lists of size N
def CutListInChunksOfSize(l, n):
    n = max(1, n)
    return (l[i:i + n] for i in range(0, len(l), n))


# This is a utility function that prints the entropy grid in a userfriendly format
def PrintEntropyGridStatus():
    PrintEntropyGrid = []
    for i in range(OutputGridSize[0] * OutputGridSize[1]):
        Value = 1
        if EntropyGrid.has_key(i):
            Value = EntropyGrid[i]
        PrintEntropyGrid.append(Value)

    print
    list(CutListInChunksOfSize(PrintEntropyGrid, OutputGridSize[0]))


def assign_wave_to_output():
    # This finds and assigns the picked PatternIndex to the output grid as attributes
    flat_out_image = []
    for x in OutputGrid.keys():
        val = next(iter(OutputGrid[x]))
        flat_out_image.append(Patterns[val][0])

    out_image = []
    for i_row in range(OutputGridSize[1]):
        current_row_position = i_row * OutputGridSize[0]
        pixel_row = flat_out_image[current_row_position: current_row_position + OutputGridSize[0]]
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


# This runs the actual WFC solve
def run_wfc_solve():
    Running = True
    while Running:

        # Find the cell with the lowest entropy value, and assign a random valid PatternIndex
        lowest_entropy_cell = get_lowest_entropy_cell()
        pattern_index_for_cell = get_random_allowed_patternIndex_from_cell(lowest_entropy_cell)
        assign_pattern_to_cell(lowest_entropy_cell, pattern_index_for_cell)

        # Propagate the OutputGrid after collapsing the LowestEntropyCell
        Running, Error = propagate_grid_cells(lowest_entropy_cell)

        # Check if all cells in the OutputGrid have collapsed yet (done solving)
        if len(EntropyGrid.keys()) == 0:
            Running = False

    # Check if we have ran into an error. (contradiction while propagating)
    if Error == 1:
        return False
    else:
        return True


def solve_wfc(image,
              output_size=(10, 10),
              seed=0,
              patter_size=3,
              periodic_input=True,
              rotate_patterns=True,
              tiling_output=False,
              max_number_contradiction_tries=1):

    global InputGridSize, OutputGridSize, InputSampleAttributes, PeriodicInput, AddRotations, N, TileAroundBounds

    InputGridSize = image.shape
    OutputGridSize = output_size
    InputSampleAttributes = image.reshape(-1, 4).tolist()
    PeriodicInput = periodic_input
    AddRotations = rotate_patterns
    N = patter_size
    TileAroundBounds = tiling_output

    for solve_attempt in range(max_number_contradiction_tries):

        # Set the seed for our random picking of values
        np.random.seed(seed + solve_attempt * 100)

        # Initialize WFC process
        create_patterns_from_input()
        initialize_grid()
        initialize_entropy_grid()
        calculate_adjacencies()

        if respect_user_constraints:
            success = ForceUserConstraints()
        else:
            success = True

        if success:
            # Run the WFC solve itself
            success = run_wfc_solve()

        # Assign the output values
        if success:
            return assign_wave_to_output()

    # If we have exceeded the number of retries for the solve, we will throw an error to tell the user no solution has been found
    raise RuntimeError("Looks like solution for current input parameters can't be found. "
                       "Try to change seed or number of contradiction tries")


# TODO:
# 1. Allow certain pieces to only instantiate once"	)
