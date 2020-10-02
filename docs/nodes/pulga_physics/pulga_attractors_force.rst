Pulga Attractors Force
====================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
Points that will Attract/Repel the system particles (vertices)


Input
-----

**Location**: Position of the attractor points.

**Max. Distance**: Distance under the force will be applied.

**Decay**: How the force will decay with distance. 0= no decay, 1= linear, 2= cubic, 4= quadratic...


Examples
--------

Trajectories of vertices repelled by three locations:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_attractors_force/blender_sverchok_pulga_attractors_force_example_01.png


Trajectories of vertices attracted by three locations:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_attractors_force/blender_sverchok_pulga_attractors_force_example_02.png
