KDT Closest Edges
=================

*Alias: KDTree Edges*

.. image:: https://user-images.githubusercontent.com/14288520/196486631-373996a4-c49a-48f8-a03b-71919988efd8.png
  :target: https://user-images.githubusercontent.com/14288520/196486631-373996a4-c49a-48f8-a03b-71919988efd8.png

.. image:: https://user-images.githubusercontent.com/14288520/196487746-16ac4469-f108-4e28-b8e8-3e65ea7005fe.png
  :target: https://user-images.githubusercontent.com/14288520/196487746-16ac4469-f108-4e28-b8e8-3e65ea7005fe.png

.. image:: https://user-images.githubusercontent.com/14288520/196505056-fd750650-f7ba-4f94-9a7e-1225e9a165c6.png
  :target: https://user-images.githubusercontent.com/14288520/196505056-fd750650-f7ba-4f94-9a7e-1225e9a165c6.png

Functionality
-------------

On each update it takes an incoming pool of Vertices and places them in a K-dimensional Tree.
It will return the Edges it can make between those vertices pairs that satisfy the constraints
imposed by the 4 parameters.

Inputs
------

- Verts, a pool of vertices to iterate through

Parameters
----------

+------------+-------+-----------------------------------------------------------+
| Parameter  | Type  | Description                                               |
+============+=======+===========================================================+
| mindist    | float | Minimum Distance to accept a pair                         |
+------------+-------+-----------------------------------------------------------+
| maxdist    | float | Maximum Distance to accept a pair                         |
+------------+-------+-----------------------------------------------------------+
| maxNum     | int   | Max number of edges to associate with the incoming vertex |
+------------+-------+-----------------------------------------------------------+
| Skip       | int   | Skip first n found matches if possible                    |
+------------+-------+-----------------------------------------------------------+

Fast Mode
---------

This mode requires Scipy dependency. It can be from 3 to 10 times faster but lacks of 'maxNum' and 'Skip' properties

.. image:: https://user-images.githubusercontent.com/14288520/196498573-c789eeb7-6ddc-4aad-9fae-c6c7b9fd137f.png
  :target: https://user-images.githubusercontent.com/14288520/196498573-c789eeb7-6ddc-4aad-9fae-c6c7b9fd137f.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/196499791-72a36288-0e0e-4e36-b97f-40c77b50d1f8.png
  :target: https://user-images.githubusercontent.com/14288520/196499791-72a36288-0e0e-4e36-b97f-40c77b50d1f8.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Circle </nodes/generator/circle>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/196500183-959e0a23-ed56-4640-b9a0-b3bc5e481d42.gif
  :target: https://user-images.githubusercontent.com/14288520/196500183-959e0a23-ed56-4640-b9a0-b3bc5e481d42.gif

---------

Max Queries Mode
----------------

This mode requires Scipy dependency. In this mode the maxNum property is used to determine how many points will be verified so it will produce less connections that the complete mode

.. image:: https://user-images.githubusercontent.com/14288520/196501322-5df056cf-653b-46d2-899c-a1ba1b098f7e.png
  :target: https://user-images.githubusercontent.com/14288520/196501322-5df056cf-653b-46d2-899c-a1ba1b098f7e.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/196503091-0bef1667-1129-4e6b-bb09-d9013de2a9f1.gif
  :target: https://user-images.githubusercontent.com/14288520/196503091-0bef1667-1129-4e6b-bb09-d9013de2a9f1.gif

---------

No Skip Mode
------------

This mode requires Scipy dependency. This is similar to the existing mode but the way the maximum connections is coded produces different results sorting the filter by minimum vertex index

.. image:: https://user-images.githubusercontent.com/14288520/196502262-6ad08724-44e2-4210-895b-1b41721386a7.png
  :target: https://user-images.githubusercontent.com/14288520/196502262-6ad08724-44e2-4210-895b-1b41721386a7.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Outputs
-------

- Edges, which can connect the pool of incoming Verts to each other.
