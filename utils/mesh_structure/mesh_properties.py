# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from typing import Any
from abc import ABC, abstractmethod


class ElementUserAttributes:
    def __init__(self):
        super().__init__()
        self._user_attrs = dict()

    def get_attribute(self, name: str) -> Any:
        if name in self._user_attrs:
            values = getattr(self, name, None)
            if values:
                return values
        raise AttributeError(f"Attribute={name} does not found in element={self}")

    def set_attribute(self, name: str, value: Any, owner_id: int):
        self._user_attrs[name] = owner_id
        setattr(self, name, value)

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
