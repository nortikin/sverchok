import numpy
import math
import itertools

# from hilbertcurve.hilbertcurve import HilbertCurve


class Contradiction(Exception):
  """Solving could not proceed without backtracking/restarting."""
  pass


class TimedOut(Exception):
  """Solve timed out."""
  pass


def make_wave(n, w, h, ground=None):
    """
    It creates 3d bool array of output image size with all possible tile variants
    :param n: number of unique patterns
    :param w: output width
    :param h: output height
    :param ground:
    :return: 3d bool array, first axis keep bool 2d output matrices for each unique pattern
    """
    wave = numpy.ones((n, w, h), dtype=bool)
    if ground is not None:
        wave[:, :, h-1] = 0
        for g in ground:
            wave[g, :, ] = 0
            wave[g, :, h-1] = 1
    return wave


def make_adj(adj_lists):
    """
    Convert adjacent list to adjacent matrix
    :param adj_lists: map of directions and lists of sets of adjacent pattern indexes
    :return: map of direction and adjacent 2D bool matrices,
    if matrix[pattern1.index, pattern2.index] == True then pattern 1 is adjacent to pattern 2
    """
    adj_matrices = {}
    num_patterns = len(list(adj_lists.values())[0])
    for direction in adj_lists:
        m = numpy.zeros((num_patterns, num_patterns), dtype=bool)
        for i, js in enumerate(adj_lists[direction]):
            for j in js:
                m[i, j] = 1
        adj_matrices[direction] = m
    return adj_matrices


######################################
# Location Heuristics

def makeRandomLocationHeuristic(preferences):
    def randomLocationHeuristic(wave):
        unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
        cell_weights = numpy.where(unresolved_cell_mask, preferences, numpy.inf)
        row, col = numpy.unravel_index(numpy.argmin(cell_weights), cell_weights.shape)
        return [row, col]
    return randomLocationHeuristic


def makeEntropyLocationHeuristic(preferences):
    def entropyLocationHeuristic(wave):
        unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
        cell_weights = numpy.where(unresolved_cell_mask, preferences + numpy.count_nonzero(wave, axis=0), numpy.inf)
        row, col = numpy.unravel_index(numpy.argmin(cell_weights), cell_weights.shape)
        return [row, col]
    return entropyLocationHeuristic


def makeAntiEntropyLocationHeuristic(preferences):
    def antiEntropyLocationHeuristic(wave):
        unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
        cell_weights = numpy.where(unresolved_cell_mask, preferences + numpy.count_nonzero(wave, axis=0), -numpy.inf)
        row, col = numpy.unravel_index(numpy.argmax(cell_weights), cell_weights.shape)
        return [row, col]
    return antiEntropyLocationHeuristic


def spiral_transforms():
    for N in itertools.count(start=1):
        if N % 2 == 0:
            yield (0, 1) # right
            for i in range(N):
                yield (1, 0) # down
            for i in range(N):
                yield (0, -1) # left
        else:
            yield (0, -1) # left
            for i in range(N):
                yield (-1, 0) # up
            for i in range(N):
                yield (0, 1) # right


def spiral_coords(x, y):
    yield x,y
    for transform in spiral_transforms():
        x += transform[0]
        y += transform[1]
        yield x,y


def fill_with_curve(arr, curve_gen):
    arr_len = numpy.prod(arr.shape)
    fill = 0
    for idx, coord in enumerate(curve_gen):
        #print(fill, idx, coord)
        if fill < arr_len:
            try:
                arr[coord[0], coord[1]] = fill / arr_len
                fill += 1
            except IndexError:
                pass
        else:
            break
    #print(arr)
    return arr


def makeSpiralLocationHeuristic(preferences):
    # https://stackoverflow.com/a/23707273/5562922

    spiral_gen = (sc for sc in spiral_coords(preferences.shape[0] // 2, preferences.shape[1] // 2))

    cell_order = fill_with_curve(preferences, spiral_gen)

    def spiralLocationHeuristic(wave):
        unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
        cell_weights = numpy.where(unresolved_cell_mask, cell_order, numpy.inf)
        row, col = numpy.unravel_index(numpy.argmin(cell_weights), cell_weights.shape)
        return [row, col]

    return spiralLocationHeuristic


def makeHilbertLocationHeuristic(preferences):
    curve_size = math.ceil( math.sqrt(max(preferences.shape[0], preferences.shape[1])))
    print(curve_size)
    curve_size = 4
    h_curve = HilbertCurve(curve_size, 2)

    def h_coords():
        for i in range(100000):
            #print(i)
            try:
              coords = h_curve.coordinates_from_distance(i)
            except ValueError:
                coords = [0,0]
            #print(coords)
            yield coords

    cell_order = fill_with_curve(preferences, h_coords())
    #print(cell_order)

    def hilbertLocationHeuristic(wave):
        unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
        cell_weights = numpy.where(unresolved_cell_mask, cell_order, numpy.inf)
        row, col = numpy.unravel_index(numpy.argmin(cell_weights), cell_weights.shape)
        return [row, col]

    return hilbertLocationHeuristic


def simpleLocationHeuristic(wave):
    unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
    cell_weights = numpy.where(unresolved_cell_mask, numpy.count_nonzero(wave, axis=0), numpy.inf)
    row, col = numpy.unravel_index(numpy.argmin(cell_weights), cell_weights.shape)
    return [row, col]


def lexicalLocationHeuristic(wave):
    unresolved_cell_mask = (numpy.count_nonzero(wave, axis=0) > 1)
    cell_weights = numpy.where(unresolved_cell_mask, 1.0, numpy.inf)
    row, col = numpy.unravel_index(numpy.argmin(cell_weights), cell_weights.shape)
    return [row, col]

#####################################
# Pattern Heuristics

def lexicalPatternHeuristic(weights):
    return numpy.nonzero(weights)[0][0]


def makeWeightedPatternHeuristic(weights):
    num_of_patterns = len(weights)
    def weightedPatternHeuristic(wave, _):
        # TODO: there's maybe a faster, more controlled way to do this sampling...
        weighted_wave = (weights * wave)
        weighted_wave /= weighted_wave.sum()
        result = numpy.random.choice(num_of_patterns, p=weighted_wave)
        return result
    return weightedPatternHeuristic


def makeRandomPatternHeuristic(weights):
    num_of_patterns = len(weights)
    def randomPatternHeuristic(wave, _):
        # TODO: there's maybe a faster, more controlled way to do this sampling...
        weighted_wave = (1.0 * wave)
        weighted_wave /= weighted_wave.sum()
        result = numpy.random.choice(num_of_patterns, p=weighted_wave)
        return result
    return randomPatternHeuristic


######################################
# Global Constraints

def make_global_use_all_patterns():
    def global_use_all_patterns(wave):
        """Returns true if at least one instance of each pattern is still possible."""
        return numpy.all(numpy.any(wave, axis=(1,2)))
    return global_use_all_patterns


#####################################
# Solver

def propagate(wave, adj, periodic=False):
    """
    :param wave: 3 dimensional bool matrix, first axis - tiles, 2-3 axises keep output bool greed
    :param adj: map of directions and 2D bool adjacency matrices
    :param periodic: if True the input wraps at the edges
    :return: None
    """
    last_count = wave.sum()

    while True:
        supports = {}
        if periodic:
            padded = numpy.pad(wave, ((0, 0), (1, 1), (1, 1)), mode='wrap')
        else:
            padded = numpy.pad(wave, ((0, 0), (1, 1), (1, 1)), mode='constant', constant_values=True)

        for direction in adj:
            dx, dy = direction
            shifted = padded[:, 1 + dx: 1 + wave.shape[1] + dx, 1 + dy: 1 + wave.shape[2] + dy]
            supports[direction] = (adj[direction] @ shifted.reshape(shifted.shape[0], -1)).reshape(shifted.shape) > 0

        for direction in adj:
            wave *= supports[direction]

        if wave.sum() == last_count:
            break
        else:
            last_count = wave.sum()

    if wave.sum() == 0:
        raise Contradiction


def observe(wave, location_heuristic, pattern_heuristic):
    i, j = location_heuristic(wave)
    pattern = pattern_heuristic(wave[:, i, j], wave)
    return pattern, i, j


def run(wave, adj, location_heuristic, pattern_heuristic, periodic=False, backtracking=False, check_feasible=None, depth_limit=5000):

    if check_feasible:
        if not check_feasible(wave):
            raise Contradiction
    propagate(wave, adj, periodic=periodic)

    depth = 0
    while wave.sum() > wave.shape[1] * wave.shape[2] and depth <= depth_limit:
        depth += 1

        if check_feasible:
            if not check_feasible(wave):
                raise Contradiction

        if depth % 50 == 0:
            print(depth)

        original = wave.copy()
        try:
            pattern, i, j = observe(wave, location_heuristic, pattern_heuristic)
            wave[:, i, j] = False
            wave[pattern, i, j] = True

            propagate(wave, adj, periodic=periodic)

        except Contradiction:
            if backtracking:
                wave = original
                wave[pattern, i, j] = False
            else:
                raise

    if depth_limit and depth > depth_limit:
        raise TimedOut
    else:
        return numpy.argmax(wave, 0)
