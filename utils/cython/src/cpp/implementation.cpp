#include "implementation.hpp"
#include <cassert>

extern "C"
{
  #include <DNA_mesh_types.h>
  #include <DNA_meshdata_types.h>
};

void some_namespace::test(std::uintptr_t mesh_ptr, std::vector<Vector3D> const& vert_poses)
{
    Mesh* mesh = reinterpret_cast<Mesh*>(mesh_ptr);
    assert(vert_poses.size() == mesh->totvert && "Размер массива не совпадает с количеством вершин.");

    for (int i = 0; i < mesh->totvert; ++i)
    {
        MVert* vert = &mesh->mvert[i];
        vert->co[0] = vert_poses[i].x;
        vert->co[1] = vert_poses[i].y;
        vert->co[2] = vert_poses[i].z;
    }
}
