Pulga Timed Force
=================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9805d1e5-4d87-446a-aba1-4e01fde2f4bd
  :target: https://github.com/nortikin/sverchok/assets/14288520/9805d1e5-4d87-446a-aba1-4e01fde2f4bd

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The inputted force will only be applied between the defined iterations range.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/abd5e0f4-aa64-4031-9b69-52297e705eff
  :target: https://github.com/nortikin/sverchok/assets/14288520/abd5e0f4-aa64-4031-9b69-52297e705eff


Input
-----

* **Force**: Force to apply the time restriction to.
* **Start**: Start iteration when the force will be applied.
* **End**: End iteration when the force will stop being applied.


Examples
--------

Example of description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4e729e08-2c52-44da-85fe-87c0081a858b
  :target: https://github.com/nortikin/sverchok/assets/14288520/4e729e08-2c52-44da-85fe-87c0081a858b

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Fields-> :doc:`Rotation Field </nodes/field/rotation_field>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Vector Force </nodes/pulga_physics/pulga_vector_force>`
* Pulga Physics-> :doc:`Pulga Random Force </nodes/pulga_physics/pulga_random_force>`

--------

In the following example a :doc:`Random Force </nodes/pulga_physics/pulga_random_force>` will be applied on the first 50 iterations, after a :doc:`Fit Force </nodes/pulga_physics/pulga_fit_force>` will be applied.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0ec9a10d-59e9-4dde-a52e-d4e885913db5
  :target: https://github.com/nortikin/sverchok/assets/14288520/0ec9a10d-59e9-4dde-a52e-d4e885913db5

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Frame Info </nodes/scene/frame_info_mk2>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Random Force </nodes/pulga_physics/pulga_random_force>`
* Pulga Physics-> :doc:`Pulga Fit Force </nodes/pulga_physics/pulga_fit_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f9d0587b-42bc-4afe-bbc4-11300a9bda03
  :target: https://github.com/nortikin/sverchok/assets/14288520/f9d0587b-42bc-4afe-bbc4-11300a9bda03