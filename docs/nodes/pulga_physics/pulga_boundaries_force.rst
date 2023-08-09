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

.. _FreeCAD: ../../solids.rst


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