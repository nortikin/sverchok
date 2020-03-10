Edge Boom
=========

Functionality
-------------

This node splits the input mesh object into separate edges objects; it can be
used to create a separate object from each edge of the input mesh.

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

Replace each edge of a square with a segment with subdivisions:

.. image:: https://user-images.githubusercontent.com/284644/76330373-942f2b80-630f-11ea-95ee-0c1f5f398e72.png

Move each edge of input objects randomly:

.. image:: https://user-images.githubusercontent.com/284644/76344998-5dafdb80-6324-11ea-9ff3-12ce2bf496c5.png

