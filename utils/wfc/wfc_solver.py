import numpy
import sys
import math
import itertools

# from hilbertcurve.hilbertcurve import HilbertCurve


# By default Python has a very low recursion limit.
# Might still be better to rewrite te recursion as a loop, of course
sys.setrecursionlimit(5500)


class Contradiction(Exception):
  """Solving could not proceed without backtracking/restarting."""
  pass


class TimedOut(Exception):
  """Solve timed out."""
  pass


class StopEarly(Exception):
  """Aborting solve early."""
  pass


def make_wave(n, w, h, ground=None):
    wave = numpy.ones((n, w, h), dtype=bool)
    if ground is not None:
        wave[:, :, h-1] = 0
        for g in ground:
            wave[g, :, ] = 0
            wave[g, :, h-1] = 1
    return wave


def make_adj(adj_lists):
    adj_matrices = {}
    num_patterns = len(list(adj_lists.values())[0])
    for d in adj_lists:
        m = numpy.zeros((num_patterns, num_patterns), dtype=bool)
        for i, js in enumerate(adj_lists[d]):
            for j in js:
                m[i, j] = 1
        adj_matrices[d] = m
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

def makeRarestPatternHeuristic(weights):
    """Return a function that chooses the rarest (currently least-used) pattern."""
    num_of_patterns = len(weights)
    def weightedPatternHeuristic(wave, total_wave):
        print(total_wave.shape)
        #[print(e) for e in wave]
        wave_sums = numpy.sum(total_wave, (1,2))
        #print(wave_sums)
        selected_pattern = numpy.random.choice(numpy.where(wave_sums == wave_sums.max())[0])
        return selected_pattern
    return weightedPatternHeuristic



def makeMostCommonPatternHeuristic(weights):
    """Return a function that chooses the most common (currently most-used) pattern."""
    num_of_patterns = len(weights)
    def weightedPatternHeuristic(wave, total_wave):
        print(total_wave.shape)
        #[print(e) for e in wave]
        wave_sums = numpy.sum(total_wave, (1,2))
        selected_pattern = numpy.random.choice(numpy.where(wave_sums == wave_sums.min())[0])
        return selected_pattern
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

def propagate(wave, adj, periodic=False, onPropagate=None):
    last_count = wave.sum()

    while True:
        supports = {}
        if periodic:
            padded = numpy.pad(wave,((0,0),(1,1),(1,1)), mode='wrap')
        else:
            padded = numpy.pad(wave,((0,0),(1,1),(1,1)), mode='constant',constant_values=True)

        for d in adj:
            dx,dy = d
            shifted = padded[:,1+dx:1+wave.shape[1]+dx,1+dy:1+wave.shape[2]+dy]
            #print(f"shifted: {shifted.shape} | adj[d]: {adj[d].shape} | d: {d}")
            #raise StopEarly
            #supports[d] = numpy.einsum('pwh,pq->qwh', shifted, adj[d]) > 0
            supports[d] = (adj[d] @ shifted.reshape(shifted.shape[0], -1)).reshape(shifted.shape) > 0

        for d in adj:
            wave *= supports[d]

        if wave.sum() == last_count:
            break
        else:
            last_count = wave.sum()

    if onPropagate:
        onPropagate(wave)

    if wave.sum() == 0:
        raise Contradiction


def observe(wave, location_heuristic, pattern_heuristic):
    i, j = location_heuristic(wave)
    pattern = pattern_heuristic(wave[:, i, j], wave)
    return pattern, i, j


def run(wave, adj, locationHeuristic, patternHeuristic, periodic=False, backtracking=False, onBacktrack=None, onChoice=None, onObserve=None, onPropagate=None, checkFeasible=None, onFinal=None, depth=0, depth_limit=None):
    #print("run.")
    if checkFeasible:
        if not checkFeasible(wave):
            raise Contradiction
        if depth_limit:
            if depth > depth_limit:
              raise TimedOut
    if depth % 50 == 0:
        print(depth)
    original = wave.copy()
    propagate(wave, adj, periodic=periodic, onPropagate=onPropagate)
    try:
        pattern, i, j = observe(wave, locationHeuristic, patternHeuristic)
        if onChoice:
            onChoice(pattern, i, j)
        wave[:, i, j] = False
        wave[pattern, i, j] = True
        if onObserve:
            onObserve(wave)
        propagate(wave, adj, periodic=periodic, onPropagate=onPropagate)
        if wave.sum() > wave.shape[1] * wave.shape[2]:
            #return run(wave, adj, locationHeuristic, patternHeuristic, periodic, backtracking, onBacktrack)
            return run(wave, adj, locationHeuristic, patternHeuristic, periodic=periodic, backtracking=backtracking, onBacktrack=onBacktrack, onChoice=onChoice, onObserve=onObserve, onPropagate=onPropagate, checkFeasible=checkFeasible, depth=depth+1, depth_limit=depth_limit)
        else:
            if onFinal:
              onFinal(wave)
            return numpy.argmax(wave, 0)
    except Contradiction:
        if backtracking:
            if onBacktrack:
                onBacktrack()
            wave = original
            wave[pattern, i, j] = False
            return run(wave, adj, locationHeuristic, patternHeuristic, periodic=periodic, backtracking=backtracking, onBacktrack=onBacktrack, onChoice=onChoice, onObserve=onObserve, onPropagate=onPropagate, checkFeasible=checkFeasible, depth=depth+1, depth_limit=depth_limit)
        else:
            if onFinal:
                onFinal(wave)
            raise
