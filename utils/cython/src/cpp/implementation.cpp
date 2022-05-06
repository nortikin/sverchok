#include "implementation.hpp"
#include <cassert>

extern "C"
{
  #include <DNA_mesh_types.h>
  #include <DNA_meshdata_types.h>
};

void some_namespace::test(std::uintptr_t mesh_ptr, float verts[])
{
    Mesh* mesh = reinterpret_cast<Mesh*>(mesh_ptr);
    // assert(vert_poses.size() == mesh->totvert && "Размер массива не совпадает с количеством вершин.");

    for (int i = 0; i < mesh->totvert; ++i)
    {
        MVert* vert = &mesh->mvert[i];
        int si = i*3;
        vert->co[0] = verts[si];
        vert->co[1] = verts[si+1];
        vert->co[2] = verts[si+2];
    }
}
