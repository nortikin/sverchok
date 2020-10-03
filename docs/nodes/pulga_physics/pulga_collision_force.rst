Pulga Collision Force
=====================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The force will be applied when de particles (vertices) are nearer than the sum of particle radius.
The force direction will be the difference of the verts location
The force magnitude will be:  (Distance - Radius Sum) * Force Strength

Input
-----

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

Options
-------

**Mode**: Algorithm used to calculate collisions. Offers 'Brute Force' and 'Kd-tree'

- Kd-tree: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed.

- Brute-Force: This mode is much slower but does not need any dependencies to work.

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_collision_force/blender_sverchok_pulga_collision_force_example_01.png
