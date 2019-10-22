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

    def __init__(self, mesh: 'DCELMesh', point: 'Point', face: 'Face' = ...) -> None: 
        self.loop_hedges: List['HalfEdge'] = None
        self.ccw_hedges: List['HalfEdge'] = None
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

class DCELMesh:
    Point: ClassVar['Point']
    HalfEdge: ClassVar['HalfEdge']
    Face: ClassVar['Face']
    accuracy: float
    points: List['Point']
    hedges: List['HalfEdge']
    faces: List['Face']
    
    def __init__(self, accuracy: Union[float, int]) -> None: ...
    
    def set_accuracy(cls, accuracy: Union[float, int]) -> None: ...
    
    def from_sv_faces(self, verts: List[TSVPoint], 
                      faces: List[TSVFace], 
                      face_mask: List[Union[bool, int]] = ...,
                      face_data: Dict[str, list] = ...) -> None: ...
    
    def to_sv_mesh(self) -> Tuple[List[TSVPoint], List[TSVFace]]: ...