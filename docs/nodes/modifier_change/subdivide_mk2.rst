Subdivide
=========

.. image:: https://user-images.githubusercontent.com/14288520/200410871-b8a74be8-67a1-42e2-b325-c11ef8265324.png
  :target: https://user-images.githubusercontent.com/14288520/200410871-b8a74be8-67a1-42e2-b325-c11ef8265324.png

Functionality
-------------

This node applies Blender's Subdivide operation to the input mesh.

.. image:: https://user-images.githubusercontent.com/14288520/200410895-0fc85b34-903f-474f-9dac-5576005c3be2.png
  :target: https://user-images.githubusercontent.com/14288520/200410895-0fc85b34-903f-474f-9dac-5576005c3be2.png

Please note that of options available differs from usual editing operator.

.. image:: https://user-images.githubusercontent.com/14288520/200531018-022c07da-27dc-4c69-acbc-b3e6bc978aac.png
  :target: https://user-images.githubusercontent.com/14288520/200531018-022c07da-27dc-4c69-acbc-b3e6bc978aac.png

Inputs
------

This node has the following inputs:

- **Vertrices**
- **Edges**. For this node to produce interesting result, this input must be provided.
- **Faces**
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
- **EdgeMask**. Selected edges to be subdivided. Faces surrounded by subdivided edges can optionally be subdivided too.
- **Number of Cuts**. Number of cuts per edge to make
- **Smooth**. Displaces subdivisions to maintain approximate curvature
- **Fractal**. Displaces the vertices in random directions after the mesh is subdivided
- **Along normal**. Causes the vertices to move along the their normals, instead of random directions
- **Seed**. Random seed

Parameters
----------

This node has the following parameters:

- **Show Old**. If checked, then outputs with "old" geometry will be shown. By default not checked.
- **Show New**. If checked, then outputs with newly created geometry will be shown. By default not checked.
- **Show Options**. If checked, then following parameters will be shown on the node itself. Otherwise, they will be available only in the N panel. By default not checked.
- **Falloff**. Smooth falloff type. Please refer to examples below for demonstration.
- **Corner cut type**. This controls the way quads with only two adjacent selected edges are subdivided (see Blender docs https://docs.blender.org/manual/en/latest/modeling/meshes/editing/edge/subdivide.html ). Available values are:

  - **Inner vertices**. The selected edges are subdivided, then an edge is created between the two new vertices, creating a small triangle. This edge is also subdivided, and the “inner vertex” thus created is linked by another edge to the one opposite to the original selected edges. All this results in a quad subdivided in a triangle and two quads
  - **Path**. First an edge is created between the two opposite ends of the selected edges, dividing the quad in two triangles. Then, the same goes for the involved triangle as described above
  - **Fan**. The quad is subdivided in a fan of four triangles, the common vertex being the one opposite to the selected edges.
  - **Straight Cut**. The selected edges are subdivided, then an edge is created between the two new vertices, creating a small triangle and n-gon

- **Grid fill**. If checked, then fully-selected faces will be filled with a grid (subdivided). Otherwise, only edges will be subdivided, not faces. Checked by default.
- **Only Quads**. If checked, then only quad faces will be subdivided, other will not. By default not checked.
- **Single edge**. If checked, tessellate the case of one edge selected in a quad or triangle. By default not checked.
- **Even smooth**. Maintain even offset when smoothing. By default not checked.
- **Number of Cuts**. Specifies the number of cuts per edge to make. By default this is 1, cutting edges in half. A value of 2 will cut it into thirds, and so on. This parameter can be also provided as input.
- **Smooth**. Displaces subdivisions to maintain approximate curvature, The effect is similar to the way the Subdivision Surface Modifier might deform the mesh. This parameter can be also provided as input.
- **Fractal**. Displaces the vertices in random directions after the mesh is subdivided. This parameter can be also provided as input.
- **Along normal**. If set to 1, causes the vertices to move along the their normals, instead of random directions. Values between 0 and 1 lead to intermediate results. This parameter can be also provided as input.
- **Seed**. Random seed. This parameter can be also provided as input.

* **Smooth Falloff**:

.. image:: https://user-images.githubusercontent.com/14288520/200430940-5b98cb7f-f150-4d4b-af7d-1611395b6746.png
  :target: https://user-images.githubusercontent.com/14288520/200430940-5b98cb7f-f150-4d4b-af7d-1611395b6746.png

* **Corner Type** (red color - selected edges):

.. image:: https://user-images.githubusercontent.com/14288520/200433213-506ae4fa-d1ee-40dc-ab82-fafc0f7083d4.gif
  :target: https://user-images.githubusercontent.com/14288520/200433213-506ae4fa-d1ee-40dc-ab82-fafc0f7083d4.gif

* **Options**:

.. image:: https://user-images.githubusercontent.com/14288520/200429430-f89ef07a-cbd6-4320-9647-96429eed4043.png
  :target: https://user-images.githubusercontent.com/14288520/200429430-f89ef07a-cbd6-4320-9647-96429eed4043.png

* **Options/ Even Smooth**:
  
.. image:: https://user-images.githubusercontent.com/14288520/200432453-57adb7d4-5c7d-4f03-b14d-8b5d27e1cb40.gif
  :target: https://user-images.githubusercontent.com/14288520/200432453-57adb7d4-5c7d-4f03-b14d-8b5d27e1cb40.gif

* **Smooth**:

.. image:: https://user-images.githubusercontent.com/14288520/200430007-b3cf9622-650e-4b49-8d7a-ef4a96d4c478.png
  :target: https://user-images.githubusercontent.com/14288520/200430007-b3cf9622-650e-4b49-8d7a-ef4a96d4c478.png

* **Fractal, Along Normal**:

.. image:: https://user-images.githubusercontent.com/14288520/200431682-b58f900b-0aad-4323-973f-b6ee40c42f17.png
  :target: https://user-images.githubusercontent.com/14288520/200431682-b58f900b-0aad-4323-973f-b6ee40c42f17.png

Advanced parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node slower but can make faster the next nodes). Available for Vertices, Edges and Pols

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Faces**. All faces of resulting mesh.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.
- **NewVertices**. All vertices that were created by subdivision. This output is only visible when **Show New** parameter is checked.
- **NewEdges**. Edges that were created by subdividing faces. This output is only visible when **Show New** parameter is checked.
- **NewFaces**. Faces that were created by subdividing faces. This output is only visible when **Show New** parameter is checked.
- **OldVertices**. Only vertices that were created on previously existing edges. This output is only visible when **Show Old** parameter is checked.
- **OldEdges**. Only edges that were created by subdividing existing edges. This output is only visible when **Show Old** parameter is checked.
- **OldFaces**. Only faces that were created by subdividing existing faces. This output is only visible when **Show Old** parameter is checked.

**Note**: Indicies in **NewEdges**, **NewFaces**, **OldEdges**, **OldFaces** outputs relate to vertices in **Vertices** output.

.. image:: https://user-images.githubusercontent.com/14288520/200675164-539055af-62a4-4faf-9c54-6756b42144e2.png
  :target: https://user-images.githubusercontent.com/14288520/200675164-539055af-62a4-4faf-9c54-6756b42144e2.png

Examples of usage
-----------------

The simplest example, subdivide a cube:

.. image:: https://user-images.githubusercontent.com/14288520/200676196-fee3e1da-6bfe-4751-96dc-45e72be95680.png
  :target: https://user-images.githubusercontent.com/14288520/200676196-fee3e1da-6bfe-4751-96dc-45e72be95680.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Subdivide one face of a cube, with smoothing:

.. image:: https://user-images.githubusercontent.com/14288520/200689133-d01920a5-b01e-4b9f-bd75-de5350b7ae0b.png
  :target: https://user-images.githubusercontent.com/14288520/200689133-d01920a5-b01e-4b9f-bd75-de5350b7ae0b.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :ref:`Select Mesh Elements (By normal and direction)<MODE_BY_NORMAL_DIRECTION>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Subdivide a cube, with smooth falloff type = Smooth:

.. image:: https://user-images.githubusercontent.com/14288520/200689719-998f9cf7-efcb-4a38-93a7-a4228a466b18.png
  :target: https://user-images.githubusercontent.com/14288520/200689719-998f9cf7-efcb-4a38-93a7-a4228a466b18.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Subdivide a torus, with smooth falloff type = Sphere:

.. image:: https://user-images.githubusercontent.com/14288520/200691209-82cced0a-5977-46bf-aa2a-0646ebb08bf6.png
  :target: https://user-images.githubusercontent.com/14288520/200691209-82cced0a-5977-46bf-aa2a-0646ebb08bf6.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
