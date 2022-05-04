class Mesh:
    __slots__ = ('verts', 'edges', 'faces_start', 'faces_total', 'loop_vert', 'loop_edge')

    def __init__(self):
        self.verts = []
        self.edges = []
        self.faces_start = []
        self.faces_total = []
        self.loop_vert = []
        self.loop_edge = []

    def __copy__(self):
        """Should be used whenever node modifies any mesh data to prevent accumulation effect
        new attribute should be a different object, data which is not modified can stay unchanged"""
        new_me = type(self)()
        for attr in self.__slots__:
            setattr(new_me, attr, getattr(self, attr))
        return new_me

    def __repr__(self):
        return f'<Mesh: verts={len(self.verts)}, edges={len(self.edges)}, faces={len(self.faces_start)}>'

    def __len__(self):
        return 1
