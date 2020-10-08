Pulga Random Force
==================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The node will apply a random force to each vertex of the defined magnitude that can change every iteration.


Input
-----

**Strength**: Magnitude of the random force.

**Variation**: Variation on every iteration. 0= no variation, 1= 100% variation.

**Seed**: Random seed. Evert number will produce different forces.


Examples
--------

Trajectories of vertices with constant random force (blue) and variating random force (green).

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_random_force/blender_sverchok_pulga_random_force_example.png
