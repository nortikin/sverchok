import numpy as np

from .wfc_tiles import make_tile_catalog
from .wfc_patterns import pattern_grid_to_tiles, make_pattern_catalog_with_rotations
from .wfc_adjacency import adjacency_extraction
from .wfc_solver import run, make_wave, make_adj, lexicalLocationHeuristic, lexicalPatternHeuristic, makeWeightedPatternHeuristic, Contradiction, makeEntropyLocationHeuristic, make_global_use_all_patterns, makeRandomLocationHeuristic, makeRandomPatternHeuristic, TimedOut, simpleLocationHeuristic, makeSpiralLocationHeuristic, makeHilbertLocationHeuristic, makeAntiEntropyLocationHeuristic
from .wfc_visualize import tile_grid_to_image


def execute_wfc(
        img,
        tile_size=1,
        pattern_width=2,
        rotations=8,
        output_size=(48, 48),
        ground=None,
        attempt_limit=10,
        output_periodic=True,
        input_periodic=True,
        loc_heuristic="entropy",
        choice_heuristic="weighted",
        global_constraint=False,
        backtracking=False):

    rotations -= 1  # change to zero-based
    img = img[:, :, :3]  # TODO: handle alpha channels

    # TODO: generalize this to more than the four cardinal directions
    direction_offsets = list(enumerate([(0, -1), (1, 0), (0, 1), (-1, 0)]))

    tile_catalog, tile_grid, code_list, unique_tiles = make_tile_catalog(img, tile_size)

    pattern_catalog, pattern_weights, pattern_list, pattern_grid = make_pattern_catalog_with_rotations(tile_grid, pattern_width, input_is_periodic=input_periodic, rotations=rotations)

    adjacency_relations = adjacency_extraction(pattern_catalog, direction_offsets, [pattern_width, pattern_width])

    number_of_patterns = len(pattern_weights)

    decode_patterns = dict(enumerate(pattern_list))
    encode_patterns = {x: i for i, x in enumerate(pattern_list)}

    adjacency_list = dict()
    # map of directions and lists of sets of pattern indexes
    # each set in the list is related with one of unique pattern
    # so it means with which patterns current pattern is adjacent in current direction
    for i, direction in direction_offsets:
        adjacency_list[direction] = [set() for _ in range(number_of_patterns)]

    for relation in adjacency_relations:
        direction = relation[0]
        pattern_id1 = relation[1]
        pattern_id2 = relation[2]
        adjacency_for_currant_direction = adjacency_list[direction]
        adjacency_for_current_pattern = adjacency_for_currant_direction[encode_patterns[pattern_id1]]
        adjacency_for_current_pattern.add(encode_patterns[pattern_id2])

    ### Ground ###

    ground_list = []
    if ground is not None:
        ground_list = np.vectorize(lambda x: encode_patterns[x])(pattern_grid.flat[(ground - 1):])
    if len(ground_list) < 1:
        ground_list = None

    wave = make_wave(number_of_patterns, output_size[0], output_size[1], ground=ground_list)
    adjacency_matrix = make_adj(adjacency_list)

    ### Heuristics ###

    encoded_weights = np.zeros(number_of_patterns, dtype=np.float64)
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

    combined_constraints = [active_global_constraint, makeSearchLengthLimit(2200)]

    def combinedConstraints(wave):
        return all([fn(wave) for fn in combined_constraints])

    ### Solving ###

    attempts = 0
    while attempts < attempt_limit:
        attempts += 1

        try:
            solution = run(wave.copy(),
                           adjacency_matrix,
                           location_heuristic=location_heuristic,
                           pattern_heuristic=pattern_heuristic,
                           periodic=output_periodic,
                           backtracking=backtracking,
                           check_feasible=combinedConstraints)

            solution_as_ids = np.vectorize(lambda x: decode_patterns[x])(solution)
            solution_tile_grid = pattern_grid_to_tiles(solution_as_ids, pattern_catalog)
            new_image = tile_grid_to_image(solution_tile_grid, tile_catalog, [tile_size, tile_size])

        except TimedOut as err:
            raise err
        except Contradiction as err:
            raise err

        if new_image is not None:
            alpha_chanel = np.ones(list(new_image.shape[:2]) + [1])
            return np.concatenate((new_image, alpha_chanel), axis=2)

    raise TimeoutError("Did not manage to build an image")
