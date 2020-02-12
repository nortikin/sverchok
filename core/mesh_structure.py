# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from dataclasses import dataclass, field


class Mesh:

    def __init__(self):
        self.name = 'Sv mesh'

        self._verts = Verts()
        self._edges = Edges()
        self._faces = Faces()
        self._loops = Loops()

    @property
    def verts(self):
        return self._verts

    @property
    def edges(self):
        return self._edges

    @property
    def faces(self):
        return self._faces

    @property
    def loops(self):
        return self._loops

    def sv_deep_copy(self) -> 'Mesh': ...


class Iterable:

    def __bool__(self) -> bool: ...

    def __len__(self) -> int: ...

    def __iter__(self) -> 'Iterable': ...

    def __next__(self) -> tuple: ...


@dataclass
class Verts(Iterable):
    co: list = field(default_factory=list)
    uv: list = field(default_factory=list)


@dataclass
class Edges(Iterable):
    ind: list = field(default_factory=list)


@dataclass
class Faces(Iterable):
    ind: list = field(default_factory=list)
    material_ind: list = field(default_factory=list)


@dataclass
class Loops(Iterable):
    pass
