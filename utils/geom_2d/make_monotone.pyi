from typing import Tuple, List, Union

TSVPoint: Tuple[float, float, float]
TSVEdge: Tuple[int, int]
TSVFace: List[int]


def monotone_sv_face_with_holes(vert_face: List[Tuple[float, float, float]], 
                                vert_holes: List[Tuple[float, float, float]] = ...,
                                face_holes: List[List[int]] = ..., 
                                accuracy: Union[float, int] = ...)\
                                -> Tuple[List[Tuple[float, float, float]], List[List[int]]]: ...
