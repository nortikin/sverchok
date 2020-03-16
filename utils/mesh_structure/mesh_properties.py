# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from dataclasses import dataclass
from typing import Any, NamedTuple, Callable, Dict
from abc import ABC, abstractmethod

import numpy as np


PY_TO_NP_TYPES = {int: np.int32, float: np.float32}


class InputFixingProps(NamedTuple):
    method_noniterable: Callable
    method_iterable: Callable
    output_dimensions_noniterable: int = 0  # <- 0 means output value is not (float or int) numpy array
    output_dimensions_iterable: int = 2  # <- 1 means array like [1,2,3,4], 2 means like [[1,2],[3,4]]


@dataclass
class UserAttribute:
    name: str
    value: Any
    for_iterable: bool
    user_id: int  # id(mesh)

    def fix(self):
        self.name = self.name.lower()
        attr_properties = self._fixing_data.get(self.name, None)
        if not attr_properties:
            return
        elif self.for_iterable:
            if attr_properties.output_dimensions_iterable:
                self.value = attr_properties.method_iterable(self.value, attr_properties.output_dimensions_iterable)
            else:
                self.value = attr_properties.method_iterable(self.value)
        else:
            if attr_properties.output_dimensions_noniterable:
                self.value = attr_properties.method_noniterable(self.value, attr_properties.output_dimensions_noniterable)
            else:
                self.value = attr_properties.method_noniterable(self.value)

    @property
    def _fixing_data(self):
        return {'name': InputFixingProps(self._extract_string, self._extract_string, 0, 0),
                'materials': InputFixingProps(self._extract_strings, self._extract_strings, 0, 0),
                'vertex_colors': InputFixingProps(self._extract_np_array, self._extract_np_array, 1, 2),
                'material_index': InputFixingProps(self._extract_value, self._extract_np_array, 0, 1)}

    def _extract_string(self, input_val):
        if isinstance(input_val, str):
            return input_val
        elif hasattr(input_val, '__iter__'):
            return self._extract_string(input_val[0])
        else:
            raise TypeError(f"Name attribute expect string value or list of strings, {input_val} got instead")

    def _extract_strings(self, input_val):
        if isinstance(input_val, str):
            return [input_val]
        elif isinstance(input_val[0], str):
            return input_val
        elif hasattr(input_val[0], '__iter__'):
            return self._extract_strings(input_val[0])
        else:
            raise TypeError(f"String values was not found in data={input_val}")

    def _extract_np_array(self, input_val, dimension=2):
        if isinstance(input_val, np.ndarray):
            if input_val.dtype == np.float:
                if input_val.dtype != np.float32:
                    input_val = np.asarray(input_val, np.float32)
            if input_val.ndim != dimension:
                if input_val.ndim == 1:
                    return input_val[None, ]
                elif input_val.ndim == 2:
                    return np.ravel(input_val)
                else:
                    raise ValueError(f"Unexpected shape of given array={input_val.shape}")
            else:
                return input_val
        real_dimension = self._len_dimension(input_val)
        if real_dimension == dimension and isinstance(self._get_last_noniterable(input_val), (int, float)):
            return np.array(input_val, dtype=PY_TO_NP_TYPES[type(self._extract_value(input_val))])
        elif real_dimension > dimension:
            nested_item = [it for i, it in zip(range(real_dimension - dimension), self._iter_first_items(input_val))][-1]
            return np.array(nested_item, dtype=PY_TO_NP_TYPES[type(self._extract_value(input_val))])
        raise TypeError(f"Can't convert data into numpy array - {input_val}")

    def _extract_value(self, input_val):
        if isinstance(input_val, (float, int)):
            return input_val
        elif hasattr(input_val, '__iter__'):
            return self._extract_value(input_val[0])
        else:
            raise TypeError(f"Int or float values was not found in data={input_val}")

    def _len_dimension(self, val: Any):
        dimension = 0
        for _ in self._iter_first_items(val):
            dimension += 1
        return dimension

    def _get_last_noniterable(self, val: Any):
        last_val = None
        for it in self._iter_first_items(val):
            last_val = it
        return last_val if last_val is not None else val

    def _iter_first_items(self, val: Any):
        if isinstance(val, str):
            return StopIteration
        try:
            yield val[0]
            yield from self._iter_first_items(val[0])
        except TypeError:
            return StopIteration


class UserAttributes:
    def __init__(self):
        super().__init__()
        self._user_attrs: Dict[str, int] = dict()

    def get_attribute(self, name: str) -> Any:
        if name in self._user_attrs:
            values = getattr(self, name, None)
            if values:
                return values
        raise AttributeError(f"Attribute={name} does not found in element={self}")

    def set_attribute(self, name: str, value: Any, owner_id: int):
        self._user_attrs[name] = owner_id
        setattr(self, name, value)

    def set_user_attribute(self, attr: UserAttribute):
        self._user_attrs[attr.name] = attr.user_id
        setattr(self, attr.name, attr.value)

    def has_attribute(self, name: str) -> bool:
        return name in self._user_attrs


class Iterable(ABC):

    def __bool__(self) -> bool:
        return bool(len(self._main_attr))

    def __len__(self) -> int:
        return len(self._main_attr)

    def __iter__(self) -> 'Iterable':
        return iter(self._main_attr)

    def __getitem__(self, item):
        return self._main_attr[item]

    @property
    @abstractmethod
    def _main_attr(self): ...
