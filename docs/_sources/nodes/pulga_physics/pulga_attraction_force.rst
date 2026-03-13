Pulga Attraction Force
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/021f3670-9c2c-4380-8f18-8da7847c541b
  :target: https://github.com/nortikin/sverchok/assets/14288520/021f3670-9c2c-4380-8f18-8da7847c541b

Functionality
-------------

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/625ed986-40aa-4f10-95b3-545c06bfc890
      :target: https://github.com/nortikin/sverchok/assets/14288520/625ed986-40aa-4f10-95b3-545c06bfc890

    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`

This node creates a force to be applied with the Pulga Physics Solver node.

The force will be applied when de particles (vertices) are farer than the sum of particle radius.

The force direction will be the difference of the vertices location

The force magnitude will be:  1/(Distance to the power of Decay) * Masses product * Force Strength


Input
-----

- **Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.
- **Decay**: How the force decays with distance (regular gravity will have a decay value of 2)
- **Max Distance**: Distance under the force will be applied.

Options
-------

**Mode**: Algorithm used to calculate attractions. Offers '**Brute Force**' and '**Kd-tree**'

- **Kd-tree**: this is the fastest mode but in order to work it needs '**Scipy**' and '**Cython**' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6
      :target: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6

- **Brute-Force**: This mode is much slower but does not need any dependencies to work.

**Stop on Collision**: When enabled the attraction force will be disabled when particles are colliding, preventing overlapping.

Example
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/22362156-9033-437d-aed0-b67457ba1cff
  :target: https://github.com/nortikin/sverchok/assets/14288520/22362156-9033-437d-aed0-b67457ba1cff

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
