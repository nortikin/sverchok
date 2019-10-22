from typing import Tuple, List, Union

TSVPoint = Tuple[float, float, float]
TSVEdge = Tuple[int, int]
TSVFace = List[int]


def monotone_sv_face_with_holes(vert_face: List[TSVPoint], 
                                vert_holes: List[TSVPoint] = ...,
                                face_holes: List[TSVFace] = ..., 
                                accuracy: Union[float, int] = ...)\
                                -> Tuple[List[TSVPoint], List[TSVFace]]: ...
