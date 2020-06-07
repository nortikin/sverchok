import numpy as np
import time

from .wfc_tiles import make_tile_catalog
from .wfc_patterns import pattern_grid_to_tiles, make_pattern_catalog_with_rotations
from .wfc_adjacency import adjacency_extraction
from .wfc_solver import run, make_wave, make_adj, lexicalLocationHeuristic, lexicalPatternHeuristic, makeWeightedPatternHeuristic, Contradiction, StopEarly, makeEntropyLocationHeuristic, make_global_use_all_patterns, makeRandomLocationHeuristic, makeRandomPatternHeuristic, TimedOut, simpleLocationHeuristic, makeSpiralLocationHeuristic, makeHilbertLocationHeuristic, makeAntiEntropyLocationHeuristic
from .wfc_visualize import tile_grid_to_image


def execute_wfc(img, tile_size=1, pattern_width=2, rotations=8, output_size=(48, 48), ground=None, attempt_limit=10, output_periodic=True, input_periodic=True, loc_heuristic="lexical", choice_heuristic="weighted", global_constraint=False, backtracking=False):
    time_begin = time.time()

    rotations -= 1  # change to zero-based

    input_stats = {"tile_size": tile_size, "pattern_width": pattern_width, "rotations": rotations, "output_size": output_size, "ground": ground, "attempt_limit": attempt_limit, "output_periodic": output_periodic, "input_periodic": input_periodic, "location heuristic": loc_heuristic, "choice heuristic": choice_heuristic, "global constraint": global_constraint, "backtracking":backtracking}

    img = img[:, :, :3]  # TODO: handle alpha channels

    # TODO: generalize this to more than the four cardinal directions
    direction_offsets = list(enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]))

    tile_catalog, tile_grid, code_list, unique_tiles = make_tile_catalog(img, tile_size)

    pattern_catalog, pattern_weights, pattern_list, pattern_grid = make_pattern_catalog_with_rotations(tile_grid, pattern_width, input_is_periodic=input_periodic, rotations=rotations)

    adjacency_relations = adjacency_extraction(pattern_grid, pattern_catalog, direction_offsets, [pattern_width, pattern_width])

    number_of_patterns = len(pattern_weights)

    decode_patterns = dict(enumerate(pattern_list))
    encode_patterns = {x: i for i, x in enumerate(pattern_list)}

    adjacency_list = {}
    for i, d in direction_offsets:
        adjacency_list[d] = [set() for i in pattern_weights]

    for i in adjacency_relations:
        adjacency_list[i[0]][encode_patterns[i[1]]].add(encode_patterns[i[2]])

    time_adjacency = time.time()

    ### Ground ###

    ground_list = []
    if ground is not None:
        ground_list = np.vectorize(lambda x: encode_patterns[x])(pattern_grid.flat[(ground - 1):])
    if len(ground_list) < 1:
        ground_list = None

    wave = make_wave(number_of_patterns, output_size[0], output_size[1], ground=ground_list)
    adjacency_matrix = make_adj(adjacency_list)

    ### Heuristics ###

    encoded_weights = np.zeros((number_of_patterns), dtype=np.float64)
    for w_id, w_val in pattern_weights.items():
        encoded_weights[encode_patterns[w_id]] = w_val
    choice_random_weighting = np.random.random(wave.shape[1:]) * 0.1

    pattern_heuristic = lexicalPatternHeuristic
    if choice_heuristic == "rarest":
        pattern_heuristic = makeRarestPatternHeuristic(encoded_weights)
    if choice_heuristic == "weighted":
        pattern_heuristic = makeWeightedPatternHeuristic(encoded_weights)
    if choice_heuristic == "random":
        pattern_heuristic = makeRandomPatternHeuristic(encoded_weights)

    location_heuristic = lexicalLocationHeuristic
    if loc_heuristic == "anti-entropy":
        location_heuristic = makeAntiEntropyLocationHeuristic(choice_random_weighting)
    if loc_heuristic == "entropy":
        location_heuristic = makeEntropyLocationHeuristic(choice_random_weighting)
    if loc_heuristic == "random":
        location_heuristic = makeRandomLocationHeuristic(choice_random_weighting)
    if loc_heuristic == "simple":
        location_heuristic = simpleLocationHeuristic
    if loc_heuristic == "spiral":
        location_heuristic = makeSpiralLocationHeuristic(choice_random_weighting)
    if loc_heuristic == "hilbert":
        location_heuristic = makeHilbertLocationHeuristic(choice_random_weighting)


    ### Visualization ###

    visualize_choice, visualize_wave, visualize_backtracking, visualize_propagate, visualize_final = None, None, None, None, None

    ### Global Constraints ###
    active_global_constraint = lambda wave: True
    if global_constraint == "allpatterns":
        active_global_constraint = make_global_use_all_patterns()

    ### Search Depth Limit
    def makeSearchLengthLimit(max_limit):
        search_length_counter = 0
        def searchLengthLimit(wave):
            nonlocal search_length_counter
            search_length_counter += 1
            return search_length_counter <= max_limit
        return searchLengthLimit

    combined_constraints = [active_global_constraint, makeSearchLengthLimit(1200)]

    def combinedConstraints(wave):
        return all([fn(wave) for fn in combined_constraints])

    ### Solving ###

    time_solve_start = None
    time_solve_end = None

    solution_tile_grid = None
    attempts = 0
    while attempts < attempt_limit:
        attempts += 1
        end_early = False
        time_solve_start = time.time()
        stats = {}
        new_image = None

        try:
            solution = run(wave.copy(),
                           adjacency_matrix,
                           locationHeuristic=location_heuristic,
                           patternHeuristic=pattern_heuristic,
                           periodic=output_periodic,
                           backtracking=backtracking,
                           onChoice=visualize_choice,
                           onBacktrack=visualize_backtracking,
                           onObserve=visualize_wave,
                           onPropagate=visualize_propagate,
                           onFinal=visualize_final,
                           checkFeasible=combinedConstraints)

            solution_as_ids = np.vectorize(lambda x: decode_patterns[x])(solution)
            solution_tile_grid = pattern_grid_to_tiles(solution_as_ids, pattern_catalog)

            new_image = tile_grid_to_image(solution_tile_grid, tile_catalog, [tile_size, tile_size])

            time_solve_end = time.time()
            stats.update({"outcome":"success"})

        except StopEarly:
            end_early = True
            stats.update({"outcome": "skipped"})
        except TimedOut:
            stats.update({"outcome": "timed_out"})
        except Contradiction:
            stats.update({"outcome": "contradiction"})

        outstats = {}
        outstats.update(input_stats)
        solve_duration = time.time() - time_solve_start
        try:
            solve_duration = (time_solve_end - time_solve_start)
        except TypeError:
            pass
        adjacency_duration = 0
        try:
            adjacency_duration = time_solve_start - time_adjacency
        except TypeError:
            pass
        outstats.update({"attempts": attempts, "time_start": time_begin, "time_adjacency": time_adjacency, "adjacency_duration": adjacency_duration, "time solve start": time_solve_start, "time solve end": time_solve_end, "solve duration": solve_duration, "pattern count": number_of_patterns})
        outstats.update(stats)
        if new_image is not None:
            alpha_chanel = np.ones(list(new_image.shape[:2]) + [1])
            return np.concatenate((new_image, alpha_chanel), axis=2)
        if end_early:
            return None

    return None
