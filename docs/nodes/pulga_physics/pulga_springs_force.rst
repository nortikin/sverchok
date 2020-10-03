Pulga Springs Force
===================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The springs are defined as edges indices.
The force direction the direction of the edge.
The force magnitude will be:  (Spring Length - Spring Rest Length) * Stiffness

Input
-----

**Springs**: Edges Indices referring to the particle system vertices.

**Stiffness**: Stiffness of the springs, if multiple values are given the will be use as stiffness per spring.

**Rest Length**: Springs rest length, if set to 0 the rest length will be calculated from the initial position.

**Clamp**: Constrain maximum difference each iteration. If set to 0 no clap will be applied

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_springs_force/blender_sverchok_pulga_springs_force_example_01.png
