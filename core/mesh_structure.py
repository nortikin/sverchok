# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE


from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from typing import List


class Mesh:

    def __init__(self):
        self.name: str = 'Sv mesh'
        self.materials: List[str] = []

        self._verts = Verts()
        self._edges = Edges()
        self._faces = Faces()
        self._loops = Loops()

    def __repr__(self):
        return f"<SvMesh: name='{self.name}', verts={len(self.verts.co)}, edges={len(self.edges.ind)}, faces={len(self.faces.ind)}>"

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

    @verts.setter
    def verts(self, verts):
        self._verts.co = verts

    @edges.setter
    def edges(self, edges):
        self._edges.ind = edges

    @faces.setter
    def faces(self, faces):
        self._faces.ind = faces

    def sv_deep_copy(self) -> 'Mesh': ...

    def to_bmesh(self, bm) -> None:
        bm_verts = [bm.verts.new(v) for v in self.verts]
        _ = [bm.edges.new([bm_verts[i] for i in e]) for e in self.edges]
        _ = [bm.faces.new([bm_verts[i] for i in f]) for f in self.faces]


class Iterable(ABC):

    def __bool__(self) -> bool:
        return bool(self._main_attr)

    def __len__(self) -> int:
        return len(self._main_attr)

    def __iter__(self) -> 'Iterable':
        return iter(self._main_attr)

    @property
    @abstractmethod
    def _main_attr(self): ...


@dataclass
class Verts(Iterable):
    co: list = field(default_factory=list)
    uv: list = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.co


@dataclass
class Edges(Iterable):
    ind: list = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.ind


@dataclass
class Faces(Iterable):
    ind: list = field(default_factory=list)
    material_ind: list = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.ind


@dataclass
class Loops(Iterable):
    uv: list = field(default_factory=list)

    @property
    def _main_attr(self):
        return self.uv


if __name__ == '__main__':
    me = Mesh()
    me.verts = [(0, 0, 0), (1, 0, 0), (2, 0, 0)]
    for v in me.verts:
        print(v)
    me.faces = [[0, 1, 2]]
    for f in me.faces:
        print(f)
    for e in me.edges:
        print('Empty?')
