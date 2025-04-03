Pulga Collision Force
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/211c68f3-e0b1-4de8-93f5-45bf09367729
  :target: https://github.com/nortikin/sverchok/assets/14288520/211c68f3-e0b1-4de8-93f5-45bf09367729

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

The force will be applied when de particles (vertices) are nearer than the sum of particle radius.

The force direction will be the difference of the verts location

The force magnitude will be:  (Distance - Radius Sum) * Force Strength

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0d6e942b-c487-4746-aac2-632f389fcaaf
  :target: https://github.com/nortikin/sverchok/assets/14288520/0d6e942b-c487-4746-aac2-632f389fcaaf

Input
-----

**Strength**: Multiplier of the force, if multiple values are given the will be use as strength per particle.

Options
-------

**Mode**: Algorithm used to calculate collisions. Offers '**Brute Force**' and '**Kd-tree**'

- **Kd-tree**: this is the fastest mode but in order to work it needs 'Scipy' and 'Cython' dependencies to be installed.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6
      :target: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6

- **Brute-Force**: This mode is much slower but does not need any dependencies to work.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/07394e3c-c5bc-4280-98ab-9c0e5349b839
  :target: https://github.com/nortikin/sverchok/assets/14288520/07394e3c-c5bc-4280-98ab-9c0e5349b839

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e9d04904-58a5-4e8f-b8c1-61fd51c545a5
  :target: https://github.com/nortikin/sverchok/assets/14288520/e9d04904-58a5-4e8f-b8c1-61fd51c545a5