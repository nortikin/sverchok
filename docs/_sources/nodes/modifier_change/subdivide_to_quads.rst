Subdivide to Quads
==================

.. image:: https://user-images.githubusercontent.com/14288520/200833247-ddbf8af4-f07c-4875-b83b-213a39039cb1.png
  :target: https://user-images.githubusercontent.com/14288520/200833247-ddbf8af4-f07c-4875-b83b-213a39039cb1.png

Functionality
-------------

Subdivide polygon faces to quads, similar to subdivision surface modifier.

.. image:: https://user-images.githubusercontent.com/14288520/200833257-e495d5c0-d487-4576-a8a9-85c36a35b273.png
  :target: https://user-images.githubusercontent.com/14288520/200833257-e495d5c0-d487-4576-a8a9-85c36a35b273.png

Inputs
------

This node has the following inputs:

- **Vertices**
- **Polygons**.
- **Iterations**. Subdivision levels.
- **Normal Displace**. Displacement along normal (value per iteration)
- **Center Random**. Random Displacement on face plane (value per iteration).
- **Normal Random**. Random Displacement along normal (value per iteration)
- **Random Seed**
- **Smooth**. Smooth Factor (value per iteration)
- **Vert Data Dict** Dictionary with the attributes you want to spread through the new vertices.
  The resultant values will be the interpolation of the input values. Accepts Scalars, Vectors and Colors

- **Face Data Dict** Dictionary with the attributes you want to spread through the new faces.
  The resultant values will be a copy of the base values.


Advanced parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Pols and Vert Map

Outputs
-------

This node has the following outputs:

- **Vertices**. All vertices of resulting mesh.
- **Edges**. All edges of resulting mesh.
- **Faces**. All faces of resulting mesh.
- **Vert Map**. List containing a integer related to the order the verts where created (See example Below)
  contains one item for each output mesh face.
- **Vert Data Dict**. Dictionary with the new vertices attributes.
- **Face Data Dict**. Dictionary with the new faces attributes.

Performance Note
----------------

The algorithm under this node is fully written in NumPy and the node will perform faster
if the input values (verts, polygons, vert and face attributes..) are NumPy arrays

Examples of usage
-----------------

Use of Vert Map output:

.. image:: https://user-images.githubusercontent.com/14288520/200837135-49f33107-a43b-4f22-9e65-e1c0006853e1.png
  :target: https://user-images.githubusercontent.com/14288520/200837135-49f33107-a43b-4f22-9e65-e1c0006853e1.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

Use of Vert Data Dict:

.. image:: https://user-images.githubusercontent.com/14288520/200840362-c165eb8e-5299-4614-bd9a-c1d138656788.png
  :target: https://user-images.githubusercontent.com/14288520/200840362-c165eb8e-5299-4614-bd9a-c1d138656788.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Dictionary-> :doc:`Dictionary In </nodes/dictionary/dictionary_in>`
* Dictionary-> :doc:`Dictionary Out </nodes/dictionary/dictionary_out>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/200840853-558388e1-06fa-4505-8f11-4a5eb4c936a4.gif
  :target: https://user-images.githubusercontent.com/14288520/200840853-558388e1-06fa-4505-8f11-4a5eb4c936a4.gif

---------

Use of Face Data Dict:

.. image:: https://user-images.githubusercontent.com/14288520/200843415-40ac8f8f-83d7-4d06-93c0-b66a50a8457e.png
  :target: https://user-images.githubusercontent.com/14288520/200843415-40ac8f8f-83d7-4d06-93c0-b66a50a8457e.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :ref:`Component Analyzer/Faces/Center <FACES_CENTER>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Dictionary-> :doc:`Dictionary In </nodes/dictionary/dictionary_in>`
* Dictionary-> :doc:`Dictionary Out </nodes/dictionary/dictionary_out>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Rock from a Tetrahedron:

.. image:: https://user-images.githubusercontent.com/14288520/200844999-33c31262-2588-4513-ab31-dafac43ef354.png
  :target: https://user-images.githubusercontent.com/14288520/200844999-33c31262-2588-4513-ab31-dafac43ef354.png

.. image:: https://user-images.githubusercontent.com/14288520/200845710-6b7de6a0-de15-415f-986d-5dd339817cc1.gif
  :target: https://user-images.githubusercontent.com/14288520/200845710-6b7de6a0-de15-415f-986d-5dd339817cc1.gif