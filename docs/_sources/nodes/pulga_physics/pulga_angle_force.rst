Pulga Angle Force
=================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1113aff9-3b2a-430d-8a13-0fc10e4e9516
  :target: https://github.com/nortikin/sverchok/assets/14288520/1113aff9-3b2a-430d-8a13-0fc10e4e9516

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a force to preserve the defined angles between edges or polygons


Input
-----

- **Edges**.
- **Stiffness**: Strength of the angle force.
- **Rest Angle**: Angle when the force will be 0. If 0 is the input value the rest angle will be calculated from the start position

Options
-------

**Mode**: Chose between edges and polygons, note that with Polygon Mode only two faces per edge will be used.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/532f2f65-b338-43d6-b5b5-9a9caf6fa687
  :target: https://github.com/nortikin/sverchok/assets/14288520/532f2f65-b338-43d6-b5b5-9a9caf6fa687

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Random Force </nodes/pulga_physics/pulga_random_force>`