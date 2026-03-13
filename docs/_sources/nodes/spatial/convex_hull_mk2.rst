Convex Hull
===========

.. image:: https://user-images.githubusercontent.com/14288520/202848763-aae6268b-c900-4d81-b41b-82b788618b07.png
  :target: https://user-images.githubusercontent.com/14288520/202848763-aae6268b-c900-4d81-b41b-82b788618b07.png

Functionality
-------------

Use this to skin a simple cloud of points. The algorithm is known as `Convex Hull <http://en.wikipedia.org/wiki/Convex_hull_algorithms>`_, and implemented in ``bmesh.ops.convex_hull``. 

.. image:: https://user-images.githubusercontent.com/14288520/202849112-808c0f4c-9d96-44e6-a833-14a6dc886900.gif
  :target: https://user-images.githubusercontent.com/14288520/202849112-808c0f4c-9d96-44e6-a833-14a6dc886900.gif

Input
------

*Vertices*


Outputs
-------

*Vertices* and *Polygons*. The number of vertices will be either equal or less than the original number. Any internal points to the system will be rejected and therefore not part of the output vertices. 


Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/202849248-6c2d96c3-cbaa-4f38-88a5-b6ae16feb4fc.png
  :target: https://user-images.githubusercontent.com/14288520/202849248-6c2d96c3-cbaa-4f38-88a5-b6ae16feb4fc.png

* Generator-> :doc:`Random Vector </nodes/spatial/populate_mesh_mk2>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/202849361-b398e216-9db2-4792-85f7-57158eb92e62.png
  :target: https://user-images.githubusercontent.com/14288520/202849361-b398e216-9db2-4792-85f7-57158eb92e62.png

* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/202858903-9b6bca6b-2e45-46b4-95b2-825264d3c1e4.png
  :target: https://user-images.githubusercontent.com/14288520/202858903-9b6bca6b-2e45-46b4-95b2-825264d3c1e4.png

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

2D mode:

.. image:: https://user-images.githubusercontent.com/14288520/202862429-0847cefc-1f23-445a-880e-dd7602617e11.png
  :target: https://user-images.githubusercontent.com/14288520/202862429-0847cefc-1f23-445a-880e-dd7602617e11.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Spatial-> :doc:`Populate Mesh </nodes/spatial/populate_mesh_mk2>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Modifiers->Modifier Change-> :doc:`Mesh Join </nodes/modifier_change/mesh_join_mk2>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/202862610-ff58cfeb-ce96-4cb5-a511-991c5a18d153.gif
  :target: https://user-images.githubusercontent.com/14288520/202862610-ff58cfeb-ce96-4cb5-a511-991c5a18d153.gif

Notes
-----
