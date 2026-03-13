Mesh Filter
===========

.. image:: https://user-images.githubusercontent.com/14288520/196620844-4cf39a96-a0f8-427c-bde7-f8a10aaf953a.png
  :target: https://user-images.githubusercontent.com/14288520/196620844-4cf39a96-a0f8-427c-bde7-f8a10aaf953a.png

Functionality
-------------

This node sorts vertices, edges or faces of input mesh by several available criteria: boundary vs interior, convex vs concave and so on. For each criteria, it puts "good" and "bad" mesh elements to different outputs. Also mask output is available for each criteria.

.. image:: https://user-images.githubusercontent.com/14288520/196633865-6a01676e-b9ed-489f-a158-50d287b807a5.png
  :target: https://user-images.githubusercontent.com/14288520/196633865-6a01676e-b9ed-489f-a158-50d287b807a5.png

---------

.. image:: https://user-images.githubusercontent.com/14288520/196634393-107d004a-fa42-4ab7-92c0-607a18e4e650.png
  :target: https://user-images.githubusercontent.com/14288520/196634393-107d004a-fa42-4ab7-92c0-607a18e4e650.png

---------

.. image:: https://user-images.githubusercontent.com/14288520/196637958-188fd916-dae6-43b7-b19b-baa5836e914f.png
  :target: https://user-images.githubusercontent.com/14288520/196637958-188fd916-dae6-43b7-b19b-baa5836e914f.png

*destination after Beta: Analyzers*

Inputs
------

This node has the following inputs:

- **Vertices**
- **Edges**
- **Faces**

Parameters
----------

This node has the following parameters:

- **Mode**. Which sort of mesh elements to operate on. There are three modes available: Vertices, Edges and Faces.
- **Filter**. Criteria to be used for filtering. List of criteria available depends on mode selected. See below.

Outputs
-------

Set of outputs depends on selected mode. See description of modes below.

Modes
-----

Vertices
^^^^^^^^

The following filtering criteria are available for the ``Vertices`` mode:

Wire.
    Vertices that are not connected to any faces.
Boundary.
    Vertices that are connected to boundary edges.
Interior.
    Vertices that are not wire and are not boundary.

The following outputs are used in this mode:

- **YesVertices**. Vertices that comply to selected criteria. 
- **NoVertices**. Vertices that do not comply to selected criteria.
- **VerticesMask**. Mask output for vertices. True for vertex that comly selected criteria.
- **YesEdges**. Edges that connect vertices complying to selected criteria.
- **NoEdges**. Edges that connect vertices not complying to selected criteria.
- **YesFaces**. Faces, all vertices of which comply to selected criteria.
- **NoFaces**. Faces, all vertices of which do not comply to selected criteria.

Note that since in this mode the node filters vertices, the indicies of vertices in input list are not valid for lists in ``YesVertices`` and ``NoVertices`` outputs. So in edges and faces outputs, this node takes this filtering into account. Indicies in ``YesEdges`` output are valid for list of vertices in ``YesVertices`` output, and so on.

Edges
^^^^^

The following filtering criteria are available for the ``Edges`` mode:

Wire.
  Edges that are not connected to any faces.
Boundary.
  Edges that are at the boundary of manifold part of mesh.
Interior.
  Edges that are manifold and are not boundary.
Convex.
  Edges that joins two convex faces. This criteria depends on valid face normals.
Concave.
  Edges that joins two concave faces. This criteria also depends on valid face normals.
Contiguous.
  Manifold edges between two faces with the same winding; in other words, the edges which connect faces with the same normals direction (inside or outside).

The following outputs are used in this mode:

- **YesEdges**. Edges that comply to selected criteria.
- **NoEdges**. Edges that do not comply to selected criteria.
- **Mask**. Mask output.

Faces
^^^^^

For this mode, only one filtering criteria is available: interior faces vs boundary faces. Boundary face is a face, any edge of which is boundary. All other faces are considered interior.

The following outputs are used in this mode:

- **Interior**. Interior faces.
- **Boundary**. Boundary faces.
- **BoundaryMask**. Mask output. It contains True for faces which are boundary.

Examples of usage
-----------------

Move only boundary vertices of plane grid:

.. image:: https://user-images.githubusercontent.com/14288520/196641596-f6c4e335-de95-4433-86e4-5b48da9a1a8c.png
  :target: https://user-images.githubusercontent.com/14288520/196641596-f6c4e335-de95-4433-86e4-5b48da9a1a8c.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* List->List Struct-> :doc:`List Item Insert </nodes/list_struct/item_insert>`
* List-> :doc:`Mask To Index </nodes/list_masks/mask_to_index>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

Bevel only concave edges:

.. image:: https://user-images.githubusercontent.com/14288520/196665550-f2cb5751-e5e3-46e7-9c40-a68f3b7e197f.png
  :target: https://user-images.githubusercontent.com/14288520/196665550-f2cb5751-e5e3-46e7-9c40-a68f3b7e197f.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Transform-> :doc:`Scale </nodes/transforms/scale_mk3>`
* Modifiers->Modifier Change-> :doc:`Extrude Separate Faces </nodes/modifier_change/extrude_separate>`
* CAD-> :doc:`Bevel </nodes/modifier_change/bevel>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Struct-> :doc:`List Item </nodes/list_struct/item>`
* List->List Struct-> :doc:`List Item Insert </nodes/list_struct/item_insert>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Extrude only boundary faces:

.. image:: https://user-images.githubusercontent.com/14288520/196672202-23b0fc30-8d97-46de-9a72-7b1be48293d3.png
  :target: https://user-images.githubusercontent.com/14288520/196672202-23b0fc30-8d97-46de-9a72-7b1be48293d3.png

* Generator->Generators Extended-> :doc:`Bricks Grid </nodes/generator/bricks>`
* Modifiers->Modifier Change-> :doc:`Extrude Separate Faces </nodes/modifier_change/extrude_separate>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color Input </nodes/color/color_input>`
* Logic-> :doc:`Switch </nodes/logic/switch_MK2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`