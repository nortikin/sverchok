Pulga Align Force
=================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a14c8ff6-0b9e-4887-8b23-bbbf78453732
  :target: https://github.com/nortikin/sverchok/assets/14288520/a14c8ff6-0b9e-4887-8b23-bbbf78453732

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force applies part of the velocity of the near particles (vertices) to each particle.

The generated effect is similar to the flocking behavior of groups of birds.

The force direction will be the velocity of the near vertex.

The force magnitude will be:  1/(Distance to the power of Decay) * 1/(number of vertices of the system) * Force Strength

Input
-----

- **Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.
- **Decay**: How the force decays with distance.
- **Max Distance**: Distance under the force will be applied.

Options
-------

**Mode**: Algorithm used to calculate attractions. Offers '**Brute Force**' and '**Kd-tree**'

- **Kd-tree**: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6
      :target: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6

- **Brute-Force**: This mode is much slower but does not need any dependencies to work.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4308e392-2386-4146-a409-391ea2f780ee
  :target: https://github.com/nortikin/sverchok/assets/14288520/4308e392-2386-4146-a409-391ea2f780ee

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Random Force </nodes/pulga_physics/pulga_random_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b761e016-aa50-405d-806a-1f3fdc9d158f
  :target: https://github.com/nortikin/sverchok/assets/14288520/b761e016-aa50-405d-806a-1f3fdc9d158f