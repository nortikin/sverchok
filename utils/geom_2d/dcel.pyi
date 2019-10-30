from typing import Tuple, List, Dict, Union, ClassVar, Iterable

TSVPoint = Tuple[float, float, float]
TSVEdge = Tuple[int, int]
TSVFace = List[int]

class Point:
    accuracy: float
    mesh: 'DCELMesh'
    co: TSVPoint
    hedge: Union[None, 'HalfEdge']

    def __init__(self, mesh: 'DCELMesh', co: TSVPoint) -> None: ...

class HalfEdge:
    accuracy: float
    mesh: 'DCELMesh'
    origin: 'Point'
    face: 'Face'
    twin: Union[None, 'HalfEdge']
    next: Union[None, 'HalfEdge']
    last: Union[None, 'HalfEdge']
    _slop: Union[None, float]
    flags: set
    left: Union[None, 'HalfEdge']

    def __init__(self, mesh: 'DCELMesh', point: 'Point', face: 'Face' = ...) -> None: 
        self.loop_hedges: List['HalfEdge'] = None
        self.ccw_hedges: List['HalfEdge'] = None
        self.cw_hedges: List['HalfEdge'] = None
        self.slop: float = None
        ...

class Face:
    accuracy: float
    mesh: 'DCELMesh'
    _outer: Union[None, 'HalfEdge']
    _inners: List['HalfEdge']
    select: bool
    sv_data: Dict[str, list]
    inners: List[HalfEdge]
    outer: 'HalfEdge'
    is_unbounded = bool

    def __init__(self, mesh: 'DCELMesh') -> None: ...

    def insert_holes(self, sv_verts: List[TSVPoint], sv_faces: List[TSVFace],
                     face_selection: List[Union[bool, int]] = ..., face_data: Dict[str, list] = ...) -> None: ...

    def check_mesh(self) -> None: ...

class DCELMesh:
    Point: ClassVar['Point']
    HalfEdge: ClassVar['HalfEdge']
    Face: ClassVar['Face']
    accuracy: float
    points: List['Point']
    hedges: List['HalfEdge']
    faces: List['Face']
    unbounded: 'Face'
    
    def __init__(self, accuracy: Union[float, int] = ...) -> None: ...
    
    def set_accuracy(cls, accuracy: Union[float, int]) -> None: ...
    
    def from_sv_faces(self, verts: List[TSVPoint], 
                      faces: List[TSVFace], 
                      face_selection: List[Union[bool, int]] = ...,
                      face_data: Dict[str, list] = ...) -> None: ...
    
    def to_sv_mesh(self, edges: bool = ..., faces: bool = ..., only_select: bool = ...) -> \
            Tuple[List[TSVPoint], List[TSVEdge], List[TSVFace]]: ...

    def del_face(self, face: 'Face') -> None: ...
    
    def from_sv_edges(self, verts: List[TSVPoint], edges: List[TSVEdge]) -> None: ...

    def generate_faces_from_hedges(self) -> None: ...

    def del_loose_hedges(self, flag: str) -> None: ...

def generate_dcel_mesh(mesh: 'DCELMesh',
                       verts: List[TSVPoint],
                       faces: List[TSVFace],
                       face_selection: List[Union[bool, int]] = ...,
                       face_data: Dict[str, list] = ...,
                       new_mesh: bool = ...) -> 'DCELMesh': ...