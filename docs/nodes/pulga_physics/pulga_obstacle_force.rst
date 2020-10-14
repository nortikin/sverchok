Pulga Obstacle Force
====================

Functionality
-------------

This node creates a force to be applied with the Pulga Physics Solver node.

Obstacles (meshes) that will collide with the system particles (vertices)


Input
-----

**Vertices**: Vertices of the obstacles.

**Polygons**: Polygons of the obstacles.

**Absorption**: Amount of energy that will be absorbed by the obstacle (reducing speed and acceleration). 0 means no absorption and 1 full absorption


Examples
--------

Grid of vertices colliding with a soft spherical mesh:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_obstacle_force/blender_sverchok_pulga_obstacle_force_example_01.png


Trajectories of vertices colliding with a hard spherical mesh.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/pulga_physics/pulga_obstacle_force/blender_sverchok_pulga_obstacle_force_example_02.png
