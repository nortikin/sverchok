Pulga Pin Force
===============

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force restricts the movement of the pinned verts


Input
-----

**Pins**: It will accept a Boolean list as a mask list or a Integer list as the index of the vertex to pin

**Axis**: Axis to restrict. It can be defined with the drop-down menu or a list from a list from 0 to 6 to define the axis restriction per pin. (0 = XYZ, 1 = XY, 2 = XZ, 3 = YZ, 4 = X, 5 = Y, 6 = Z )

**Pins Goal**: End position of the pinned vertices.


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_pin_force/blender_sverchok_pulga_pin_force_example_01.png

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_pin_force/blender_sverchok_pulga_pin_force_example_02.png
