Pulga Attractors Force
======================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/969228cd-c56d-4d47-8d13-a37b31319285
  :target: https://github.com/nortikin/sverchok/assets/14288520/969228cd-c56d-4d47-8d13-a37b31319285

Functionality
-------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4980768f-580e-4220-8575-73c8f5c8611d
  :target: https://github.com/nortikin/sverchok/assets/14288520/4980768f-580e-4220-8575-73c8f5c8611d

This node creates a force to be applied with the Pulga Physics Solver node.

Mode
----

Offers three different modes Point, Line and Plane with different Input sets

Point
-----

Points that will Attract/Repel the system particles (vertices)

.. image:: https://github.com/nortikin/sverchok/assets/14288520/06975305-e41f-4fa1-a13c-e5dfc4bb0928 
  :target: https://github.com/nortikin/sverchok/assets/14288520/06975305-e41f-4fa1-a13c-e5dfc4bb0928

Point Inputs
------------

- **Location**: Position of the attractor points.
- **Max. Distance**: Distance under the force will be applied.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c214a6d0-b002-482b-ace2-da3c4231cae4
      :target: https://github.com/nortikin/sverchok/assets/14288520/c214a6d0-b002-482b-ace2-da3c4231cae4

- **Decay**: How the force will decay with distance. 0= no decay, 1= linear, 2= cubic, 4= quadratic...

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c032761e-a24a-4469-99c6-13681a480436
      :target: https://github.com/nortikin/sverchok/assets/14288520/c032761e-a24a-4469-99c6-13681a480436

Line
-----

Lines that will Attract/Repel the system particles (vertices)

.. image:: https://github.com/nortikin/sverchok/assets/14288520/b6e13955-eb1c-4589-a3b2-2db0737b5f97
  :target: https://github.com/nortikin/sverchok/assets/14288520/b6e13955-eb1c-4589-a3b2-2db0737b5f97

Line Inputs
-----------

- **Location**: A point on the Line.
- **Direction**: Direction of the Line.
- **Max. Distance**: Distance under the force will be applied.
- **Decay**: How the force will decay with distance. 0= no decay, 1= linear, 2= cubic, 4= quadratic...

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/baebc767-fbdf-4260-b67c-17385f4ddda5
      :target: https://github.com/nortikin/sverchok/assets/14288520/baebc767-fbdf-4260-b67c-17385f4ddda5

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/8c607df0-407c-4480-b7fb-3574eaa35276
      :target: https://github.com/nortikin/sverchok/assets/14288520/8c607df0-407c-4480-b7fb-3574eaa35276

Plane
-----

Plane that will Attract/Repel the system particles (vertices)

.. image:: https://github.com/nortikin/sverchok/assets/14288520/907216e2-d9c9-41d5-890c-1f43743dc4dc
  :target: https://github.com/nortikin/sverchok/assets/14288520/907216e2-d9c9-41d5-890c-1f43743dc4dc

Plane Inputs
------------

- **Location**: A point on the Line.
- **Normal**: Normal of the Plane.
- **Max. Distance**: Distance under the force will be applied.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ebdaa4ce-1e41-4da6-a2d1-c7f8ef4785ed
      :target: https://github.com/nortikin/sverchok/assets/14288520/ebdaa4ce-1e41-4da6-a2d1-c7f8ef4785ed

- **Decay**: How the force will decay with distance. 0= no decay, 1= linear, 2= cubic, 4= quadratic...

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/5d935bfa-0f4c-43c0-b2d7-32e30e5671a3
      :target: https://github.com/nortikin/sverchok/assets/14288520/5d935bfa-0f4c-43c0-b2d7-32e30e5671a3

Examples
--------

Trajectories of vertices repelled by vertice in zero coords:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e8199160-7bc8-4ffa-982a-cb8cfc0eee9d
  :target: https://github.com/nortikin/sverchok/assets/14288520/e8199160-7bc8-4ffa-982a-cb8cfc0eee9d

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

--------

Trajectories of vertices repelled by 5 locations:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1d51f0c2-ab86-4d67-9904-eafdf6e7500a
  :target: https://github.com/nortikin/sverchok/assets/14288520/1d51f0c2-ab86-4d67-9904-eafdf6e7500a

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

--------

Trajectories of vertices attracted by three locations:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0fa1ce67-39b4-47f8-98c5-2a560d84f385
  :target: https://github.com/nortikin/sverchok/assets/14288520/0fa1ce67-39b4-47f8-98c5-2a560d84f385

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Pulga Physics-> :doc:`Pulga Physics Solver </nodes/pulga_physics/pulga_physics_solver>`

