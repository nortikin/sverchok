Pulga Obstacle Force
====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d60e18cd-99b0-458c-a06c-9aa3c0580864
  :target: https://github.com/nortikin/sverchok/assets/14288520/d60e18cd-99b0-458c-a06c-9aa3c0580864

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/359e71c7-205f-4a71-9a8b-51288765fb38
  :target: https://github.com/nortikin/sverchok/assets/14288520/359e71c7-205f-4a71-9a8b-51288765fb38

This node creates a force to be applied with the Pulga Physics Solver node.

Obstacles (meshes) that will collide with the system particles (vertices)


Input
-----

- **Vertices**: Vertices of the obstacles.
- **Polygons**: Polygons of the obstacles.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/58982fee-8fc5-4d1c-9f59-d74a0ce804ce
      :target: https://github.com/nortikin/sverchok/assets/14288520/58982fee-8fc5-4d1c-9f59-d74a0ce804ce
    
    * Generator-> :doc:`Box </nodes/generator/box_mk2>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

- **Absorption**: Amount of energy that will be absorbed by the obstacle (reducing speed and acceleration). 0 means no absorption and 1 full absorption

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6e1dad7e-d2e5-480e-b452-2f279835ee7a
      :target: https://github.com/nortikin/sverchok/assets/14288520/6e1dad7e-d2e5-480e-b452-2f279835ee7a

    * Number-> :doc:`Number Range </nodes/number/number_range>`
    * Vector-> :doc:`Vector In </nodes/vector/vector_in>`
    * Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

Examples
--------

Grid of vertices colliding with a soft Cylindrical mesh:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e1c0bcac-5b33-40c7-bea6-9c25c1b5b647
  :target: https://github.com/nortikin/sverchok/assets/14288520/e1c0bcac-5b33-40c7-bea6-9c25c1b5b647

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

--------

Grid of vertices colliding with a soft spherical mesh:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_obstacle_force/blender_sverchok_pulga_obstacle_force_example_01.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_obstacle_force/blender_sverchok_pulga_obstacle_force_example_01.png


* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`


--------

Trajectories of vertices colliding with a hard spherical mesh.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/da62baed-63c5-4a67-98b3-41f57f54f8f0
  :target: https://github.com/nortikin/sverchok/assets/14288520/da62baed-63c5-4a67-98b3-41f57f54f8f0

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e4e95fa6-9b2d-4c6e-8ccc-0e8754cfbac4
  :target: https://github.com/nortikin/sverchok/assets/14288520/e4e95fa6-9b2d-4c6e-8ccc-0e8754cfbac4