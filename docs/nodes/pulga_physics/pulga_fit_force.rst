Pulga Fit Force
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d9cd470f-710c-47d1-9050-2b184bcc0426
  :target: https://github.com/nortikin/sverchok/assets/14288520/d9cd470f-710c-47d1-9050-2b184bcc0426

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/40199133-8b1c-490d-abb9-318c127a2916
  :target: https://github.com/nortikin/sverchok/assets/14288520/40199133-8b1c-490d-abb9-318c127a2916

This node creates a force to be applied with the Pulga Physics Solver node.

The force will make the particles (vertices) radius to shrink when the collide or grow if the do not.

Input
-----

- **Magnitude**: Amount to grow/shrink every iteration.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/54bbf038-937a-4990-80fe-defddb0102a3
      :target: https://github.com/nortikin/sverchok/assets/14288520/54bbf038-937a-4990-80fe-defddb0102a3

    * Transform-> :doc:`Randomize </nodes/transforms/randomize>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

- **Min. Radius**: Minimum radius particles can have.
- **Max. Radius**: Maximum radius particles can have.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/14209c8f-1a42-4b9d-9f76-251afffd3736
      :target: https://github.com/nortikin/sverchok/assets/14288520/14209c8f-1a42-4b9d-9f76-251afffd3736

Options
-------

**Algorithm**: Algorithm used to calculate collisions. Offers '**Brute Force**' and '**Kd-tree**'

- **Kd-tree**: this is the fastest mode but in order to work it needs '**Scipy**' and '**Cython**' dependencies to be installed. In this mode the attraction continues even if the vertices are colliding

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6
      :target: https://github.com/nortikin/sverchok/assets/14288520/b87f2ad1-e8e3-4937-adab-6baa99c3bbc6

- **Brute-Force**: This mode is much slower but does not need any dependencies to work.

**Mode**: How the magnitude is interpreted. Offers '**Absolute**', '**Relative**' and '**Percent**'.

- **Absolute**: The magnitude will be added or subtracted as defined.
- **Relative**: The magnitude will be multiplied by the particle radius.
- **Percent**: The magnitude will be interpreted as a percent of the particle radius.


Examples
--------

Maximum radius for a set of points.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/bb29cc04-f13a-4ee6-bace-774d05d852be
  :target: https://github.com/nortikin/sverchok/assets/14288520/bb29cc04-f13a-4ee6-bace-774d05d852be

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`


    .. image:: https://github.com/nortikin/sverchok/assets/14288520/b235c925-25e9-4bb9-bf66-96916caff1a5
      :target: https://github.com/nortikin/sverchok/assets/14288520/b235c925-25e9-4bb9-bf66-96916caff1a5

  * Transform-> :doc:`Randomize </nodes/transforms/randomize>`

--------

Arranging circles with attraction and collision.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/aefc9540-e9f6-4bbf-94c6-58dc77f26362
  :target: https://github.com/nortikin/sverchok/assets/14288520/aefc9540-e9f6-4bbf-94c6-58dc77f26362

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`
* Pulga Physics-> :doc:`Pulga Attractors Force </nodes/pulga_physics/pulga_attractors_force_mk2>`
* Pulga Physics-> :doc:`Pulga Collision Force </nodes/pulga_physics/pulga_collision_force>`
* Pulga Physics-> :doc:`Pulga Drag Force </nodes/pulga_physics/pulga_drag_force>`
* Pulga Physics-> :doc:`Pulga Boundaries Force </nodes/pulga_physics/pulga_boundaries_force>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
