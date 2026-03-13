Edge Boom
=========

.. image:: https://user-images.githubusercontent.com/14288520/199942622-8e6e9a9a-7f9b-43b2-9463-15e790b49610.png
  :target: https://user-images.githubusercontent.com/14288520/199942622-8e6e9a9a-7f9b-43b2-9463-15e790b49610.png

Functionality
-------------

This node splits the input mesh object into separate edges objects; it can be
used to create a separate object from each edge of the input mesh.

.. image:: https://user-images.githubusercontent.com/14288520/199942253-4212f665-4c91-48a0-ab74-b467c6a62d6f.png
  :target: https://user-images.githubusercontent.com/14288520/199942253-4212f665-4c91-48a0-ab74-b467c6a62d6f.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of the input mesh. This input is mandatory.
- **Edges**. Edges of the input mesh. This input is optional: if it is not
  connected, **Faces** input will be used to determine object edges. But if you
  want output objects to appear in certain order, you need to connect this.
- **Faces**. Faces of the input mesh. This input is optional. This input must
  be connected if **Edges** input is not connected.

Parameters
----------

This node has the following parameters:

- **Output mode**. The following modes are available:

  * **Vertices**. For each edge of the input mesh, output the first vertex of
    the edge to the **Vertex1** output and the second vertex of the edge to the
    **Vertex2** output. This mode is the default one.
  * **Objects**. Make a separate object from each edge of the input mesh, and
    output the list of it's vertices (always 2 vertices) into **Vertices**
    output, and the list of it's edges (always 1 edge) into **Edges** output.

- **Separate**. This parameter is available only when **Output mode** is set to
  **Objects**. If checked, output separate list of edge objects per each input
  objects. Otherwise, output one flat list of edge objects for all input
  objects. Unchecked by default.
- **Sort vertices**. This parameter is available only when **Output mode** is
  set to **Vertices**. If checked, the node will sort vertices of each edge, so
  that the **Vertex1** output will always contain a vertex with index (in the
  input mesh) smaller than the index of the vertex in the **Vertex2** output.
  Checked by default.

Outputs
-------

This node has the following outputs:

- **Vertex1**. The first vertex of each edge. This output contains one vertex
  for each edge of the input object. This output is only available when the
  **Output mode** parameter is set to **Vertices**.
- **Vertex2**. The second vertex of each edge. This output contains one vertex
  for each edge of the input object. This output is only available when the
  **Output mode** parameter is set to **Vertices**.
- **Vertices**. Vertices of the objects into which the input mesh was split.
  This output contains two vertices for each edge of the input mesh. This
  output is only available when the **Output mode** parameter is set to
  **Objects**.
- **Edges**. Edges of the objects into which the input mesh was split. This
  output contains one edge for each edge of the input mesh. This output is only
  available when the **Output mode** parameter is set to **Objects**.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/199945595-9b63fd1d-1fc1-42d7-80ae-e3524161b0e8.png
  :target: https://user-images.githubusercontent.com/14288520/199945595-9b63fd1d-1fc1-42d7-80ae-e3524161b0e8.png

* Generator-> :doc:`Segment </nodes/generator/segment>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Transform-> :doc:`Scale </nodes/transforms/scale_mk3>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Replace each edge of a square with a segment with subdivisions:

.. image:: https://user-images.githubusercontent.com/14288520/199948148-a88d073c-c900-40ec-83b4-4a048ad82b58.png
  :target: https://user-images.githubusercontent.com/14288520/199948148-a88d073c-c900-40ec-83b4-4a048ad82b58.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`

---------

Move each edge of input objects randomly:

.. image:: https://user-images.githubusercontent.com/14288520/199951691-afdae55c-3e88-4adb-8526-4a9173a8bcb6.png
  :target: https://user-images.githubusercontent.com/14288520/199951691-afdae55c-3e88-4adb-8526-4a9173a8bcb6.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Random Vector </nodes/generator/random_vector_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`