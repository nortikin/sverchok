# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from typing import Any, Union

import numpy as np

import sverchok.core.mesh_structure as ms


MeshElements = Union[ms.Mesh, ms.Verts, ms.Edges, ms.Faces, ms.Loops]


def set_safe_attr(element: MeshElements, attr_name: str, val: Any) -> None:
    # It will check data before setting to a mesh instance and will correct it if need
    # Usage only for getting data from user
    attr_name = attr_name.lower()
    fixed_data = fix_input_data(element, attr_name, val)
    if fixed_data is NotImplemented:
        setattr(element, attr_name, val)
    else:
        setattr(element, attr_name, fixed_data)


class MeshInputCorrector:
    @staticmethod
    def name(input_val):
        return extract_string(input_val)

    @staticmethod
    def materials(input_val):
        return extract_strings(input_val)

    @staticmethod
    def verts(input_val):
        return extract_np_array(input_val)

    @staticmethod
    def vertex_colors(input_val):
        return extract_np_array(input_val, dimension=1)

    @staticmethod
    def material_index(input_val):
        return extract_value(input_val)


class VertsInputCorrector:
    @staticmethod
    def uv(input_val):
        return extract_np_array(input_val)

    @staticmethod
    def vertex_colors(input_val):
        return extract_np_array(input_val)


class EdgesInputCorrector:
    pass


class FacesInputCorrector:
    @staticmethod
    def vertex_colors(input_val):
        return extract_np_array(input_val)


class LoopsInputCorrector:
    @staticmethod
    def uv(input_val):
        return extract_np_array(input_val)

    @staticmethod
    def vertex_colors(input_val):
        return extract_np_array(input_val)


def fix_input_data(element: MeshElements, attr_name: str, val: Any) -> Any:
    correctors = {ms.Mesh: MeshInputCorrector,
                  ms.Verts: VertsInputCorrector,
                  ms.Edges: EdgesInputCorrector,
                  ms.Faces: FacesInputCorrector,
                  ms.Loops: LoopsInputCorrector}
    corrector = correctors.get(type(element))
    if not corrector:
        return NotImplemented
    method = getattr(corrector, attr_name, None)
    if not method:
        return NotImplemented
    return method(val)


def extract_string(input_val):
    if isinstance(input_val, str):
        return input_val
    elif hasattr(input_val, '__iter__'):
        return extract_string(input_val[0])
    else:
        raise TypeError(f"Name attribute expect string value or list of strings, {input_val} got instead")


def extract_strings(input_val):
    if isinstance(input_val, str):
        return [input_val]
    elif isinstance(input_val[0], str):
        return input_val
    elif hasattr(input_val[0], '__iter__'):
        return extract_string(input_val[0])
    else:
        raise TypeError(f"String values was not found in data={input_val}")


def extract_np_array(input_val, dimension=2):
    if isinstance(input_val, np.ndarray) and input_val.dtype == np.dtype('f') and len(input_val.shape) == dimension:
        return input_val
    real_dimension = len_dimension(input_val)
    if real_dimension == dimension and isinstance(get_last_noniterable(input_val), (int, float)):
        return np.array(input_val, dtype='f')
    elif real_dimension > dimension:
        nested_item = [it for i, it in zip(range(real_dimension - dimension), iter_first_items(input_val))][-1]
        return np.array(nested_item, dtype='f')
    raise TypeError(f"Can't convert data into numpy array - {input_val}")


def extract_value(input_val):
    if isinstance(input_val, (float, int)):
        return input_val
    elif hasattr(input_val, '__iter__'):
        return extract_value(input_val[0])
    else:
        raise TypeError(f"Int or float values was not found in data={input_val}")


def len_dimension(val: Any):
    dimension = 0
    for _ in iter_first_items(val):
        dimension += 1
    return dimension


def get_last_noniterable(val: Any):
    last_val = None
    for it in iter_first_items(val):
        last_val = it
    return last_val if last_val is not None else val


def iter_first_items(val: Any):
    if isinstance(val, str):
        return StopIteration
    try:
        yield val[0]
        yield from iter_first_items(val[0])
    except TypeError:
        return StopIteration

