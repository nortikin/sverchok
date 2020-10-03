Pulga Align Force
=================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.
The force applies part of the velocity of the near particles (vertices) to each particle.
The force direction will be the velocity of the near vertex
The force magnitude will be:  1/(Distance to the power of Decay) * 1/(number of vertices of the system) * Force Strength

Input
-----

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

**Decay**: How the force decays with distance.

**Max Distance**: Distance under the force will be applied.

Options
-------

**Mode**: Algorithm used to calculate attractions. Offers 'Brute Force' and 'Kd-tree'

- Kd-tree: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

- Brute-Force: This mode is much slower but does not need any dependencies to work.

Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_align_force/blender_sverchok_pulga_align_force_example_01.png
