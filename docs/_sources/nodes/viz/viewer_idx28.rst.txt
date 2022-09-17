Viewer Index+
=============

.. image:: https://user-images.githubusercontent.com/14288520/189987500-f9bf79a3-79a2-4250-af0d-eb98372bdde8.png
  :target: https://user-images.githubusercontent.com/14288520/189987500-f9bf79a3-79a2-4250-af0d-eb98372bdde8.png

.. image:: https://user-images.githubusercontent.com/14288520/190139465-2d5beff6-e871-4148-be65-03f47d951f24.png
  :target: https://user-images.githubusercontent.com/14288520/190139465-2d5beff6-e871-4148-be65-03f47d951f24.png

Functionality
-------------

This node's primary purpose is for display the index information of geometry and topology, it will draw the indices of ``Vertices``, ``Edges``, and ``Faces`` 

- Vertex indices are drawn on the locations of the vertices
- Edge indices are drawn on midpoint of the Edge
- Face indices are drawn at the average location of the Vertices associated with the face.

Additionally

- the input geometry can be transformed using the Matrix socket.
- the Node can draw arbitrary (non renderable) text into the 3dview at the
  location of incoming verts, edges and faces. If incoming data is shorter than
  number of elements the last element will be displayed on rest elements.

Because it can be difficult to read indices when there are many geometric elements visible there is an option to draw a small background under the text element.

Parameters
----------

Activate
  Enabling the node.

Draw background
  Hide background around text.

.. image:: https://user-images.githubusercontent.com/14288520/190143217-5cc4e457-194b-491e-9de0-2fc793d645d7.png
  :target: https://user-images.githubusercontent.com/14288520/190143217-5cc4e457-194b-491e-9de0-2fc793d645d7.png

Draw bface
  (using the Ghost icon in the Node UI) if you attach verts + faces, you can
  also hide backfacing indices from being displayed. Adding the faces
  information gives the node enough information to detect what can be seen
  directly by the viewport "eye" location.

.. image:: https://user-images.githubusercontent.com/14288520/190142052-1524e31a-a4fa-4c69-9c3c-bc0230f7cec7.png
  :target: https://user-images.githubusercontent.com/14288520/190142052-1524e31a-a4fa-4c69-9c3c-bc0230f7cec7.png

Draw object index
  (available from N Panel) the Node can display the Object index associated
  with the element ( the first object, first index will be drawn as ``0: 0`` )

.. image:: https://user-images.githubusercontent.com/14288520/190146606-ab79e7d2-00f7-4f39-b805-94a82da20d1e.png
  :target: https://user-images.githubusercontent.com/14288520/190146606-ab79e7d2-00f7-4f39-b805-94a82da20d1e.png

Examples
--------

**Hide text behind geometry**

.. image:: https://user-images.githubusercontent.com/14288520/189987936-5d24ba0b-9141-4f1e-bbd1-97f1dbad1bde.png
  :target: https://user-images.githubusercontent.com/14288520/189987936-5d24ba0b-9141-4f1e-bbd1-97f1dbad1bde.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

**Show custom text with offset**

.. image:: https://user-images.githubusercontent.com/14288520/190860803-b2bfaf38-1775-4057-8b25-06daac70a769.png
  :target: https://user-images.githubusercontent.com/14288520/190860803-b2bfaf38-1775-4057-8b25-06daac70a769.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* ROUND X: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`