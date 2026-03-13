Pulga Physics Solver
====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2dc0b37e-3267-48c0-b022-0b197c8e90d5
  :target: https://github.com/nortikin/sverchok/assets/14288520/2dc0b37e-3267-48c0-b022-0b197c8e90d5

Functionality
-------------

This node creates simulations from input parameters, it is meant to be used in form-finding purposes.
It creates the simulation using the inputted vertices as spherical particles that react to applied forces.

The node is a basic NumPy implementation of basic physics system heavily inspired in "The Nature of Code" by Daniel Shiffman
and the Kangoroo Plug-in for Grasshopper. Due the nature of the algorithm it can get very intensive, handle with responsibility

Input & Output
--------------


+------------------------+---------------+-----------------------------------------------+
| Input                  | Type          |  Description                                  |
+========================+===============+===============================================+
| **Initial_Pos**        | Vertices      | Vertices in original state                    |
+------------------------+---------------+-----------------------------------------------+
| **Iterations**         | Integer       | Number of iterations of the process           |
+------------------------+---------------+-----------------------------------------------+
| **Radius**             | Float         | Radius of virtual sphere, used to             |
|                        |               | calculate intersections, mass and surface     |
+------------------------+---------------+-----------------------------------------------+
| **Initial Velocity**   | Vertices      | Initial vertices velocity                     |
+------------------------+---------------+-----------------------------------------------+
| **Max Velocity**       | Float         | Maximum vertices velocity                     |
+------------------------+---------------+-----------------------------------------------+
| **Density**            | Float         | Particles Density                             |
+------------------------+---------------+-----------------------------------------------+
| **Forces**             | Force         | System forces                                 |
+------------------------+---------------+-----------------------------------------------+

+------------------------+---------------+-----------------------------------------------+
| Output                 | Type          |  Description                                  |
+========================+===============+===============================================+
| **Vertices**           | Vertices      | Vertices in original state                    |
+------------------------+---------------+-----------------------------------------------+
| **Radius**             | Strings       | Radius of virtual sphere, used to             |
|                        |               | calculate intersections, mass and surface     |
+------------------------+---------------+-----------------------------------------------+
| **Velocity**           | Vertices      | Velocity at the end of iterations             |
+------------------------+---------------+-----------------------------------------------+
| **Pin Reactions**       | Strings      | Reactions at Pinned Vertices                  |
+------------------------+---------------+-----------------------------------------------+

Accumulative:
-------------

When activated every nodeTree update will use the previous update as the starting point. The update can be triggered by the Update button or by any other event that triggers regular updates (like playing animation or changing any value).

It offers some options:

**Reset**: Takes back the system to the initial state.

**Update**: Runs one Node-Tree update.

**Pause**: Pauses nodes calculations and ignores ui changes.


Examples
--------

Arranging circles with attraction and collision.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f03b8e4e-a78e-4f50-9986-c3aa3a7067e7
  :target: https://github.com/nortikin/sverchok/assets/14288520/f03b8e4e-a78e-4f50-9986-c3aa3a7067e7

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
* Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
* Pulga Physics-> :doc:`Pulga Attraction Force </nodes/pulga_physics/pulga_attraction_force>`
* Pulga Physics-> :doc:`Pulga Fit Force </nodes/pulga_physics/pulga_fit_force>`
* Pulga Physics-> :doc:`Pulga Boundaries Force </nodes/pulga_physics/pulga_boundaries_force>`

Getting result in animation:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7a1022a6-c1b2-40be-a3f9-ab84a6b6bc21
  :target: https://github.com/nortikin/sverchok/assets/14288520/7a1022a6-c1b2-40be-a3f9-ab84a6b6bc21


--------

Inflating a cube simulating a pillow.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4c51f66c-bc37-4391-aeff-f41d43f5c48b
  :target: https://github.com/nortikin/sverchok/assets/14288520/4c51f66c-bc37-4391-aeff-f41d43f5c48b

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
* Pulga Physics-> :doc:`Pulga Inflate Force </nodes/pulga_physics/pulga_inflate_force>`

Animated:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/99dffb12-6355-472a-965f-f56c55c6de9f
  :target: https://github.com/nortikin/sverchok/assets/14288520/99dffb12-6355-472a-965f-f56c55c6de9f

---------

Tensile structures can be studied with pinned points.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b0a35c32-9daa-4047-9df8-3ceb9e20ab2b
  :target: https://github.com/nortikin/sverchok/assets/14288520/b0a35c32-9daa-4047-9df8-3ceb9e20ab2b

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`3pt Arc </nodes/generator/basic_3pt_arc>`
* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Analyzers-> :doc:`Path Length </nodes/analyzer/path_length_2>`
* Transform-> :doc:`Transform Select </nodes/transforms/transform_select>`
* Modifiers->Modifier Make-> :doc:`Subdivide </nodes/modifier_change/subdivide_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* MUL X, SIN, DIV: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Vector-> :doc:`Vector Rewire </nodes/vector/vector_rewire>`
* ANGLE RAD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Modifiers->Modifier Make-> :doc:`Solidify </nodes/modifier_make/solidify_mk2>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
* Pulga Physics-> :doc:`Pulga Pin Force </nodes/pulga_physics/pulga_pin_force>`\

Animated:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/fd2b45f9-60e4-4499-a001-83775f265469
  :target: https://github.com/nortikin/sverchok/assets/14288520/fd2b45f9-60e4-4499-a001-83775f265469

---------

Using the caternary as a structural modeling tool:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/279c74b2-8303-4d54-98b5-0cf1b5285b3f
  :target: https://github.com/nortikin/sverchok/assets/14288520/279c74b2-8303-4d54-98b5-0cf1b5285b3f

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Float to Integer </nodes/number/float_to_int>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Polyline Viewer </nodes/viz/polyline_viewer>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
* Pulga Physics-> :doc:`Pulga Pin Force </nodes/pulga_physics/pulga_pin_force>`

Animated:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/7b64dea0-6699-4e9b-9a55-9a9bfc0d4e2a
  :target: https://github.com/nortikin/sverchok/assets/14288520/7b64dea0-6699-4e9b-9a55-9a9bfc0d4e2a

---------

Variable spring stiffness can be used to simulate sewing springs inflatable structures.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2a68b551-4d9e-49ad-b279-4b8050f219d2
  :target: https://github.com/nortikin/sverchok/assets/14288520/2a68b551-4d9e-49ad-b279-4b8050f219d2

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Analyzers-> :doc:`Points Inside Mesh </nodes/analyzer/points_inside_mesh>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* Matrix-> :doc:`Matrix Normal </nodes/matrix/matrix_normal>`
* List-> :doc:`Mask Converter </nodes/list_masks/mask_convert>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`
* Pulga Physics-> :doc:`Pulga Inflate Force </nodes/pulga_physics/pulga_inflate_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/54853304-19cd-48f7-b88f-d403f2c0fc87
  :target: https://github.com/nortikin/sverchok/assets/14288520/54853304-19cd-48f7-b88f-d403f2c0fc87

---------

Shooting particles to a attractors field.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5286a603-f72a-44dc-950d-2b8e404b11e9
  :target: https://github.com/nortikin/sverchok/assets/14288520/5286a603-f72a-44dc-950d-2b8e404b11e9

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator->Generator Extended-> :doc:`Polygon Grid </nodes/generators_extended/polygon_grid>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List->List Struct-> :doc:`List Repeater </nodes/list_struct/repeater>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Attractors Force </nodes/pulga_physics/pulga_attractors_force_mk2>`

Animated:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6b9003a6-939b-4ad6-b760-58ce9d6023b0
  :target: https://github.com/nortikin/sverchok/assets/14288520/6b9003a6-939b-4ad6-b760-58ce9d6023b0

---------

The "Pins Reactions" output supply the resultant force on the pins. It can be use to model auxiliary structures.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/6cd54f5d-4ec9-4964-82a1-cc7b42be3f8e
  :target: https://github.com/nortikin/sverchok/assets/14288520/6cd54f5d-4ec9-4964-82a1-cc7b42be3f8e

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzers->Component Analyzer **Adjacent Edges**: :ref:`Adjacent edges<VERTICES_ADJACENT_EDGES>`
* EQUAL: Logic-> :doc:`Logic Functions </nodes/logic/logic_node>`
* List-> :doc:`Mask To Index </nodes/list_masks/mask_to_index>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`
* Pulga Physics-> :doc:`Pulga Pin Force </nodes/pulga_physics/pulga_pin_force>`

Animated

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ef3685f0-fae4-4eb7-83d8-caf6b4ce8451
  :target: https://github.com/nortikin/sverchok/assets/14288520/ef3685f0-fae4-4eb7-83d8-caf6b4ce8451