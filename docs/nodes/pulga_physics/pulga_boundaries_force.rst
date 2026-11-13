Pulga Boundaries Force
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/952405a8-ad93-4310-84a9-a90913080d2f
  :target: https://github.com/nortikin/sverchok/assets/14288520/952405a8-ad93-4310-84a9-a90913080d2f

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a constrain each vertex into a defined boundaries.

Options & Inputs
----------------

Scheme for options:

**Mode**: Defines how boundaries are defined.

- **Box**: Given a list of vertices it will calculate their bounding box and use it as limit of the simulation

  Inputs: Vertices (Bounding Box)

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/1d611b74-e8e4-4f54-878c-06991d3fe955
      :target: https://github.com/nortikin/sverchok/assets/14288520/1d611b74-e8e4-4f54-878c-06991d3fe955

    * Generator-> :doc:`Box </nodes/generator/box_mk2>`
    * Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
    * Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/fd7bf5e5-0fc9-48c9-8492-ff64b6ac4c61
      :target: https://github.com/nortikin/sverchok/assets/14288520/fd7bf5e5-0fc9-48c9-8492-ff64b6ac4c61

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ae5e14ba-5f32-4c0f-8b3f-96d4cc39f04d
      :target: https://github.com/nortikin/sverchok/assets/14288520/ae5e14ba-5f32-4c0f-8b3f-96d4cc39f04d
  
    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ef2353c4-d7c8-4bb4-9b95-fff64fad2e28
      :target: https://github.com/nortikin/sverchok/assets/14288520/ef2353c4-d7c8-4bb4-9b95-fff64fad2e28


- **Sphere**: Run the simulation into a spherical space.

  Inputs: Center and radius

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/410adf33-3c7b-47d0-943e-2af24a93615c
      :target: https://github.com/nortikin/sverchok/assets/14288520/410adf33-3c7b-47d0-943e-2af24a93615c

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
    * Transform-> :doc:`Randomize </nodes/transforms/randomize>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

  if source points inside sphere then result spread over volume of sphere:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/2a1c7f8d-b9af-43c0-adeb-fd91455b2b29
      :target: https://github.com/nortikin/sverchok/assets/14288520/2a1c7f8d-b9af-43c0-adeb-fd91455b2b29

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/854a3a7c-8c11-4655-ac05-c8ddb989dcc5
      :target: https://github.com/nortikin/sverchok/assets/14288520/854a3a7c-8c11-4655-ac05-c8ddb989dcc5

  Points out of a boundary sphere try occupy nearest surface. Points inside boundary sphere try occupy volume of boundary sphere:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c2653d81-85e6-4e89-9b99-af982017e987
      :target: https://github.com/nortikin/sverchok/assets/14288520/c2653d81-85e6-4e89-9b99-af982017e987

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
    * Transform-> :doc:`Randomize </nodes/transforms/randomize>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/2d01169c-91c2-47e9-b59b-7f56232df131
      :target: https://github.com/nortikin/sverchok/assets/14288520/2d01169c-91c2-47e9-b59b-7f56232df131

- **Sphere (Surface)**: Run the simulation into a spherical surface

  Inputs: Center and radius

  Like boundary **Sphere** but spread only on surface of boundary sphere:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/31ff3637-d9b8-49a0-b771-ece6b266efd5
      :target: https://github.com/nortikin/sverchok/assets/14288520/31ff3637-d9b8-49a0-b771-ece6b266efd5

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
    * Transform-> :doc:`Randomize </nodes/transforms/randomize>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

- **Plane**: Run the simulation into a defined plane

  Inputs: Center and Normal

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/14e61808-7c30-4a77-bb0f-f1fbd0005073
      :target: https://github.com/nortikin/sverchok/assets/14288520/14e61808-7c30-4a77-bb0f-f1fbd0005073

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
    * Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/679a2d88-e659-4281-946f-3d2651f31e5e
      :target: https://github.com/nortikin/sverchok/assets/14288520/679a2d88-e659-4281-946f-3d2651f31e5e

- **Mesh** (Surface): Run simulation in the surface of a mesh

  Inputs: Vertices and Polygons

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/8f2019ac-d819-467b-8fdc-3587373473c9
      :target: https://github.com/nortikin/sverchok/assets/14288520/8f2019ac-d819-467b-8fdc-3587373473c9

    * Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
    * Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/28f12c4a-cfa6-42d8-92f3-a76f19c53b55
      :target: https://github.com/nortikin/sverchok/assets/14288520/28f12c4a-cfa6-42d8-92f3-a76f19c53b55

- **Mesh (Volume)**: Run the simulation inside a mesh

  Inputs: Vertices and Polygons

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/4925a438-e77c-4721-8299-b25ea3cc54f0
      :target: https://github.com/nortikin/sverchok/assets/14288520/4925a438-e77c-4721-8299-b25ea3cc54f0

    * Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
    * Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * List->List Main-> :doc:`List Join </nodes/list_main/join>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
    * Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/0f0a0ddb-688e-4c17-a108-9a7572713f04
      :target: https://github.com/nortikin/sverchok/assets/14288520/0f0a0ddb-688e-4c17-a108-9a7572713f04

- **Solid (Surface)**: Run simulation in the surface of a solid (requires _FreeCAD)

  Inputs: Solid

- **Solid (Volume)**: Run the simulation inside a solid (requires _FreeCAD)

  Inputs: Solid

- **Solid Face**: Run the simulation the surface of a solid face (requires _FreeCAD)

  Inputs: Solid Face


- **Mesh (Edges)**: Constrain particles to the closest point on a mesh edge.

  Inputs: **Vertices**, **Edges**. Each particle is projected onto the closest
  segment and its velocity and resultant force are projected onto that segment's
  tangent. This is an exact projection onto the *input segments*; no Fast/Precise
  selector is necessary. Zero-length edges are ignored.

- **Curve**: Constrain particles to a Sverchok parametric curve.

  Input: **Curve**. **Method** offers:

  * **Fast**: discretize the curve once using **Resolution** points, then project
    to the nearest segment. This is fast, but the boundary is the sampled polyline.
  * **Precise** (SciPy): find a point on the original parametric curve using
    Sverchok's numerical nearest-point routine; **Initial Samples** determines
    the number of samples used to initialize the search. Numerical optimization
    is not guaranteed to find the global minimum for every curve.

  Velocity and force are projected onto the local tangent. Curve endpoints are
  part of the constraint domain.

- **Surface**: Constrain particles to a Sverchok parametric surface, from either
  side of its normal.

  Input: **Surface**. **Method** offers:

  * **Fast**: tessellate the surface once using **Resolution U** and
    **Resolution V**, build a cached BVH and project particles to its triangles.
  * **Precise** (SciPy): minimize distance to the original parametric surface,
    using independent **Initial Samples U** and **Initial Samples V** to seed
    optimization. This is slower and may converge to a local minimum.

  Velocity and force remain tangent to the surface. Both methods operate on the
  *full rectangular UV domain*; trimmed FreeCAD faces should use **Solid Face**.

.. _FreeCAD: ../../solids.rst


Solid boundaries: Fast and Precise
---------------------------------

The **Solid (Surface)**, **Solid (Volume)** and **Solid Face** modes require
FreeCAD and offer two calculation methods, with **Fast** selected by default.

- **Fast**: tessellates the FreeCAD shape once, builds a Blender BVH, and uses
  the same projection behavior as **Mesh (Surface)** or **Mesh (Volume)**.
  For **Solid Face**, the particles are projected onto the tessellated face.
  The **Deflection** socket controls tessellation precision; smaller values
  usually improve fidelity but produce more triangles and may be slower.
- **Precise**: uses the original FreeCAD B-Rep nearest-point and containment
  operations. It may be significantly slower for many particles/iterations.

The **Curve** and **Surface** modes also use **Fast** by default, with their
existing Resolution / Resolution U-V controls, and offer **Precise** with
Initial Samples / Initial Samples U-V.

For **Solid (Volume)**, the Fast method assumes a watertight, properly oriented
triangulation. If the source solid has invalid topology or an unsuitable mesh,
the inside/outside classification may be unreliable. In that case increase
tessellation precision or use **Precise**.

The Fast method uses the cached FreeCAD tessellation for the lifetime of the
force. Changing the solid or Deflection rebuilds it on the next node update.


Grouping Solid Faces
--------------------

**Solid Face** uses the socket's list nesting to define independent boundary
forces and composite boundaries:

- ``[face_a, face_b]`` creates **two forces**, one for each face.
- ``[[face_a, face_b]]`` creates **one force** from both faces.
- ``[[face_a, face_b], [face_c]]`` creates **two forces**: a composite of
  ``face_a`` and ``face_b``, followed by a separate ``face_c`` constraint.

Each force acts on **all particles of the same Pulga simulation**, and forces
are applied **in sequence**. Thus two separate noncoincident faces may still
pull all particles back and forth or collapse them toward an intersection.
Use one nested group when the intention is to constrain particles to the
nearest location on the **union of several faces**.

For each group containing more than one face:

- **Fast** constructs a FreeCAD compound, tessellates it only once and builds
  a shared Blender BVH. **Deflection** controls the approximation quality.
- **Precise** queries the compound's trimmed B-Rep geometry directly.

A group containing a single face keeps the original face object. The outer
and inner trimming wires still define the face's boundaries; this is a
surface constraint, **not** an Outer Wire-only perimeter constraint.

Examples
--------

Performing simulation in the surface of a plane and inside a mesh:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d0e52c78-8d4b-4514-ae67-0f9e2f4c6dc0
  :target: https://github.com/nortikin/sverchok/assets/14288520/d0e52c78-8d4b-4514-ae67-0f9e2f4c6dc0

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Surfaces-> :doc:`Plane (Surface) </nodes/surface/plane>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/52bc7f13-5ac3-4426-baa4-5851a1d6e322
  :target: https://github.com/nortikin/sverchok/assets/14288520/52bc7f13-5ac3-4426-baa4-5851a1d6e322


Curve boundary: particles constrained to an ellipse
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/4a3a0298-79c6-484a-ad68-c097201c9530
   :target: https://github.com/user-attachments/assets/4a3a0298-79c6-484a-ad68-c097201c9530

An **Ellipse (Curve)** defines the path that the particles must follow.
**Pulga Boundaries Force** is set to **Curve**, with the **Fast** method and a
**Resolution** of 64. The curve is sampled once and its segments are used to
project the particles back onto the approximate ellipse during simulation.
Velocity and force components normal to the boundary are removed, while
motion along the curve remains possible.

**Random Vector** creates the initial particle positions. **Pulga Physics
Solver** combines the boundary with **Pulga Fit Force**, **Pulga Collision
Force**, **Pulga Timed Force**, and **Pulga Drag Force**. These forces influence
particle size, spacing and motion, while the boundary keeps particle centers
on the discretized curve. Increasing **Resolution** improves the geometric
approximation at an additional setup cost. The **Precise** method instead
projects onto the original curve using numerical optimization (SciPy).


Surface boundary: particles constrained to a parametric surface
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. image:: https://github.com/user-attachments/assets/3f689315-a97b-4150-848d-82e915b65668
   :target: https://github.com/user-attachments/assets/3f689315-a97b-4150-848d-82e915b65668

A **Surface Formula** node creates a parametric surface with the height
expression ``sin(u)*sin(v)``. **Pulga Boundaries Force** uses **Surface** mode
and the **Fast** method with **Resolution U** and **Resolution V** set to 25.
The surface is tessellated once, and the resulting triangle mesh is used to
constrain particle positions. The boundary also removes the normal component
of particle velocity and force, allowing motion tangential to the surface.

The solver starts from randomly distributed points and combines the boundary
with **Pulga Fit Force**, **Pulga Collision Force**, and **Pulga Drag Force**.
For visualization, the resulting point arrangement is connected using
**Delaunay 2D**, producing a network over the surface. **Nearest Point on
Surface** is used in the displayed node setup for the visualization workflow;
it is not required by the boundary force itself. Increasing U/V resolution
improves the Fast approximation, while **Precise** uses numerical projection
onto the original parametric surface with independent **Initial Samples U**
and **Initial Samples V** (SciPy).
