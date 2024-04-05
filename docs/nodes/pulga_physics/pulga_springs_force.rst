Pulga Springs Force
===================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f26739ab-e00d-4f19-8f59-c050f68a9e6b
  :target: https://github.com/nortikin/sverchok/assets/14288520/f26739ab-e00d-4f19-8f59-c050f68a9e6b

Functionality
-------------

This node creates a force to be applied with the [:doc:`Pulga Physics->Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`] node.

The springs are defined as edges indices.

The force direction the direction of the edge.

The force magnitude will be:  (Spring Length - Spring Rest Length) * Stiffness

.. image:: https://github.com/nortikin/sverchok/assets/14288520/27685dc7-d85c-4101-a4b8-4d26f3285ebc
  :target: https://github.com/nortikin/sverchok/assets/14288520/27685dc7-d85c-4101-a4b8-4d26f3285ebc

Input
-----

* **Springs**: Edges Indices referring to the particle system vertices.
* **Stiffness**: Stiffness of the springs, if multiple values are given the will be use as stiffness per spring.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/353b8c64-0a3c-4dde-aa99-2ee2bafd1f17
      :target: https://github.com/nortikin/sverchok/assets/14288520/353b8c64-0a3c-4dde-aa99-2ee2bafd1f17

* **Rest Length**: Springs rest length, if set to 0 the rest length will be calculated from the initial position.
* **Clamp**: Constrain maximum difference each iteration. If set to 0 no clap will be applied

.. _PULGA_SPRINGS_FORCE_EXAMPLES:

Examples
--------

Example in description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e8c76f03-518a-458d-a2d5-3f7edf8ffb77
  :target: https://github.com/nortikin/sverchok/assets/14288520/e8c76f03-518a-458d-a2d5-3f7edf8ffb77

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/random_points_on_mesh>`
* Spatial-> :doc:`Voronoi on Mesh </nodes/spatial/voronoi_on_mesh_mk2>`
* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* Modifiers->Modifier Change-> :doc:`Merge by Distance </nodes/modifier_change/merge_by_distance>`
* Analyzers->Component Analyzer **Vertices->Sharpness**: :ref:`Vertices Sharpness<VERTICES_SHARPNESS>`
* Analyzers->Component Analyzer **Vertices->Is Boundary**: :ref:`Vertices Is Boundary<VERTICES_IS_BOUNDARY>`
* List->List Main-> :doc:`List Zip </nodes/list_main/zip>`
* List->List Main-> :doc:`List Math </nodes/list_main/func>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* List->List Main-> :doc:`List Zip </nodes/list_main/zip>`
* BIG_EQ: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Logic-> :doc:`Switch </nodes/logic/switch_MK2>`
* Color-> :doc:`Color Input </nodes/color/color_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Pin Force </nodes/pulga_physics/pulga_pin_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

Example with Cylinder:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3f80e648-2000-40ee-b87b-f064f476ba56
  :target: https://github.com/nortikin/sverchok/assets/14288520/3f80e648-2000-40ee-b87b-f064f476ba56

Example with Torus:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5c5f48fd-f612-4f8f-924a-85f0d0c9ada2
  :target: https://github.com/nortikin/sverchok/assets/14288520/5c5f48fd-f612-4f8f-924a-85f0d0c9ada2

---------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ca855c7e-d4c1-4ebb-b7bf-e087d5da2e30
  :target: https://github.com/nortikin/sverchok/assets/14288520/ca855c7e-d4c1-4ebb-b7bf-e087d5da2e30

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers->Component Analyzer: :ref:`Adjacent Edges num<VERTICES_ADJACENT_EDGES_NUM>`
* Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* List-> :doc:`Mask To Index </nodes/list_masks/mask_to_index>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Pin Force </nodes/pulga_physics/pulga_pin_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fa53b414-91e1-49b3-bfca-c46c49c72f83
  :target: https://github.com/nortikin/sverchok/assets/14288520/fa53b414-91e1-49b3-bfca-c46c49c72f83

---------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b6725122-effc-4338-ba2e-9937b9396ff9
  :target: https://github.com/nortikin/sverchok/assets/14288520/b6725122-effc-4338-ba2e-9937b9396ff9

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers->Component Analyzer **Vertices->Sharpness**: :ref:`Vertices Sharpness<VERTICES_SHARPNESS>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* List-> :doc:`Mask To Index </nodes/list_masks/mask_to_index>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Pin Force </nodes/pulga_physics/pulga_pin_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/16dd65d0-b235-4a76-aa14-69cc6aff0273
  :target: https://github.com/nortikin/sverchok/assets/14288520/16dd65d0-b235-4a76-aa14-69cc6aff0273