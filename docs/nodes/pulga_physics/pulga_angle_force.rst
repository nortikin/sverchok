Pulga Angle Force
=================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a force to preserve the defined angles between edges or polygons


Input
-----

**Edges**.

**strength**: Strength of the angle force.

**Rest Angle**: Angle when the force will be 0. If 0 is the input value the rest angle will be calculated from the start position

Options
-------

**Mode**: Chose between edges and polygons, note that with Polygon Mode only two faces per edge will be used



Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_angle_force/blender_sverchok_pulga_angle_force_example_01.png
