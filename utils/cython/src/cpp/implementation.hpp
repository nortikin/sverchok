#include <cstdint>
#include <vector>

struct Vector3D
{
    float x;
    float y;
    float z;
};

namespace some_namespace
{
    void test(std::uintptr_t mesh_ptr, std::vector<Vector3D> const& vert_poses);
}