Pulga Inflate Force
===================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a7932c90-6f7a-4ab5-8125-c812748588d2
  :target: https://github.com/nortikin/sverchok/assets/14288520/a7932c90-6f7a-4ab5-8125-c812748588d2

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/595eaef0-5c71-471e-9fc3-144ed407792b
  :target: https://github.com/nortikin/sverchok/assets/14288520/595eaef0-5c71-471e-9fc3-144ed407792b

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a force along the normal of the input polygons proportional (multiplied) to the area of the polygon.


Input
-----

- **Polygons**: Polygon Indices referring to the particle system vertices.
- **Strength**: Magnitude of the inflate force.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ba3659e9-8eb7-4b72-9281-ce6f51a3712c
      :target: https://github.com/nortikin/sverchok/assets/14288520/ba3659e9-8eb7-4b72-9281-ce6f51a3712c

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_inflate_force/blender_sverchok_pulga_inflate_force_example_01.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_inflate_force/blender_sverchok_pulga_inflate_force_example_01.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/21404503-0eaa-4865-9928-067f01ed2bfb
  :target: https://github.com/nortikin/sverchok/assets/14288520/21404503-0eaa-4865-9928-067f01ed2bfb

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Springs Force </nodes/pulga_physics/pulga_springs_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`