Pulga Attraction Force
=====================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force will be applied when de particles (vertices) are farer than the sum of particle radius.

The force direction will be the difference of the vertices location

The force magnitude will be:  1/(Distance to the power of Decay) * Masses product * Force Strength

Input
-----

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

**Decay**: How the force decays with distance (regular gravity will have a decay value of 2)

**Max Distance**: Distance under the force will be applied.

Options
-------

**Mode**: Algorithm used to calculate attractions. Offers 'Brute Force' and 'Kd-tree'

- Kd-tree: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

- Brute-Force: This mode is much slower but does not need any dependencies to work.

**Stop on Collision**: When enabled the attraction force will be disabled when particles are colliding, preventing overlapping.

Example
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_attraction_force/blender_sverchok_pulga_attraction_force_example_01.png
