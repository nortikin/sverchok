Aligned Bounding Box (Alpha)
============================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/9361e542-2804-49ff-8d5e-9b1137f2a102
  :target: https://github.com/nortikin/sverchok/assets/14288520/9361e542-2804-49ff-8d5e-9b1137f2a102

Functionality
-------------

Generates an *aligned bounding box* from incoming Vertices.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e8aeec1c-d631-409b-b695-e51e9b552226
  :target: https://github.com/nortikin/sverchok/assets/14288520/e8aeec1c-d631-409b-b695-e51e9b552226

Inputs
------

- **Vertices** - or a nested list of vertices that represent separate objects.
- **Matrix** - Matrix to align bounding box to (Rotation only. Scale and translation are not used).
- **Factor** - Interpolation between calculated aligned bounding box and a bounding box position that set by **Matrix**.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/f5fea1b7-3f48-4065-8f73-e24b516b5f02
  :target: https://github.com/nortikin/sverchok/assets/14288520/f5fea1b7-3f48-4065-8f73-e24b516b5f02

Parameters
----------

- **merge** - If bbox calculated for several meshes then its merge into one mesh. Output sockets for Matrix, Length, Width and Height has unmerged params.

Output
------

- **Vertices** - Vertices of aligned bounding bpxes
- **Edges** - Edges of aligned bounding bpxes
- **Faces** - Faces of aligned bounding bpxes
- **Matrix** - Result matrix of calculated bounding box
- **Length**, **Width**, **Height** - Size of aligned bounding box. Axises can be changed unpredictable.

Examples
--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/e46277f3-74b9-4432-b58f-6d4a56c8ca12
  :target: https://github.com/nortikin/sverchok/assets/14288520/e46277f3-74b9-4432-b58f-6d4a56c8ca12

* Generator-> :doc:`Cricket </nodes/generator/cricket>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

--------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/84588685-1360-4029-b8de-5346008b982b
  :target: https://github.com/nortikin/sverchok/assets/14288520/84588685-1360-4029-b8de-5346008b982b

* Spatial-> :doc:`Populate Mesh </nodes/spatial/random_points_on_mesh>`
* Spatial-> :doc:`Voronoi on Mesh </nodes/spatial/voronoi_on_mesh_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`

.. raw:: html

   <video width="700" controls>
     <source src="https://github.com/nortikin/sverchok/assets/14288520/0b14d7d1-6b8b-4901-b8f5-a55177658e09" type="video/mp4">
   Your browser does not support the video tag.
   </video>