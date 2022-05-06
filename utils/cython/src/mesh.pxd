from libcpp.vector cimport vector
from libc.stdint cimport uintptr_t

cdef extern from "cpp/implementation.hpp":
    struct Vector3D:
        float x
        float y
        float z

cdef extern from "cpp/implementation.hpp" namespace "some_namespace":
    void test(uintptr_t mesh_ptr, float *verts)

