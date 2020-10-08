Pulga Fit Force
===============

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force will make the particles (vertices) radius to shrink when the collide or grow if the do not.

Input
-----

**Magnitude**: Amount to grow/shrink every iteration.

**Min. Radius**: Minimum radius particles can have.

**Max. Radius**: Maximum radius particles can have.

Options
-------

**Algorithm**: Algorithm used to calculate collisions. Offers 'Brute Force' and 'Kd-tree'

- Kd-tree: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

- Brute-Force: This mode is much slower but does not need any dependencies to work.

**Mode**: How the magnitude is interpreted. Offers 'Absolute', 'Relative' and 'Percent'.

- Absolute: The magnitude will be added or subtracted as defined.

- Relative: The magnitude will be multiplied by the particle radius.

- Percent: The magnitude will be interpreted as a percent of the particle radius.


Examples
--------

Maximum radius for a set of points.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_fit_force/blender_sverchok_pulga_fit_force_example_01.png

Arranging circles with attraction and collision.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_fit_force/blender_sverchok_pulga_fit_force_example_02.png
