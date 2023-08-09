Pulga Vector Force
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ad3d3efd-64e7-400b-89cc-337a5bb1eee0
  :target: https://github.com/nortikin/sverchok/assets/14288520/ad3d3efd-64e7-400b-89cc-337a5bb1eee0

Functionality
-------------

This node creates a force to be applied with the :doc:`Pulga Physics->Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>` node.

* The force applies the inputted vector as a force to each vertex.
* The force direction will be the same as the inputted vertex.
* The force magnitude will be:  Inputted Vector Magnitude * Force Strength

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a3be3b5b-00a0-42f0-86ef-8337f9e5e28f
  :target: https://github.com/nortikin/sverchok/assets/14288520/a3be3b5b-00a0-42f0-86ef-8337f9e5e28f

Input
-----

* **Force**: Force as vector value. It will also accept a vector Field as input, if multiple values are given the will be use as force per particle.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6fb198c4-1cbf-4ed9-8e06-abf32ee373f0
      :target: https://github.com/nortikin/sverchok/assets/14288520/6fb198c4-1cbf-4ed9-8e06-abf32ee373f0

    * Fields-> :doc:`Vector Field Formula </nodes/field/vector_field_formula>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

---------

    Connect :doc:`Fields->Rotation Field </nodes/field/rotation_field>` into "Force" socket:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b89393aa-bce4-462d-b20b-ccf72d2579fe
      :target: https://github.com/nortikin/sverchok/assets/14288520/b89393aa-bce4-462d-b20b-ccf72d2579fe

    * Number-> :doc:`List Input </nodes/number/list_input>`
    * Number-> :doc:`Number Range </nodes/number/number_range>`
    * Fields-> :doc:`Rotation Field </nodes/field/rotation_field>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

* **Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/5a44434c-a46f-4113-96ae-9a8540dcc1e4
      :target: https://github.com/nortikin/sverchok/assets/14288520/5a44434c-a46f-4113-96ae-9a8540dcc1e4

---------

    Set **strength** per particle:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b12295a5-9f94-4b2f-8d72-f80655c435a2
      :target: https://github.com/nortikin/sverchok/assets/14288520/b12295a5-9f94-4b2f-8d72-f80655c435a2

    * Number-> :doc:`List Input </nodes/number/list_input>`
    * Fields-> :doc:`Rotation Field </nodes/field/rotation_field>`
    * Number-> :doc:`List Input </nodes/number/list_input>`
    * Number-> :doc:`Number Range </nodes/number/number_range>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

Options
-------

**Proportional to Mass**: multiply the Vector Force by the mass of the particle.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c4fd300e-20df-4569-82ea-3375abf358c9
      :target: https://github.com/nortikin/sverchok/assets/14288520/c4fd300e-20df-4569-82ea-3375abf358c9


Examples
--------

Description Example (Influence of some parameters):

.. image:: https://github.com/nortikin/sverchok/assets/14288520/767aec31-e800-44ad-b017-2bd2d7c20f11
  :target: https://github.com/nortikin/sverchok/assets/14288520/767aec31-e800-44ad-b017-2bd2d7c20f11

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Fields-> :doc:`Rotation Field </nodes/field/rotation_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Vector-> :doc:`Vector Polar Output </nodes/vector/vector_polar_out>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* List->List Struct-> :doc:`List Flip </nodes/list_struct/flip>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/606e9352-d2ac-4615-bf06-81b69d3d7bab
  :target: https://github.com/nortikin/sverchok/assets/14288520/606e9352-d2ac-4615-bf06-81b69d3d7bab

---------

Constant vector force:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vector_force/blender_sverchok_pulga_vector_force_example_01.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vector_force/blender_sverchok_pulga_vector_force_example_01.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Noise Vector Field as vector force:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vector_force/blender_sverchok_pulga_vector_force_example_02.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_vector_force/blender_sverchok_pulga_vector_force_example_02.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Noise Vector Field </nodes/field/noise_vfield>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`