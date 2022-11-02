Origins
=======

.. image:: https://user-images.githubusercontent.com/14288520/195716748-2e4392e9-433e-465e-bb59-6c4e67ed305f.png
  :target: https://user-images.githubusercontent.com/14288520/195716748-2e4392e9-433e-465e-bb59-6c4e67ed305f.png

Functionality
-------------

The node produces centers, normals, tangents for any element of given mesh. Also it can combine the data into matrix.
The output is close how blender is placing moving axis of selected mesh element in normal mode.

Category
--------

analyzers -> origins

Inputs
------

- **Vertices** - vertices
- **Edges** - edges (optionally)
- **Faces** - faces (optionally)

Outputs
-------

- **Origin** - center of element, in vertex mode just coordinates of current vertex
- **Normal** - normal of current element
- **Tangent** - tangent to current element
- **Matrix** - built from origin, normal and tangent data matrix

.. image:: https://user-images.githubusercontent.com/14288520/195724734-737f4fea-dfc0-4c2b-955a-3c2fe7bd3343.png
  :target: https://user-images.githubusercontent.com/14288520/195724734-737f4fea-dfc0-4c2b-955a-3c2fe7bd3343.png

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Element mode             | enum  | Vertex, edge or face                                                           |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Flat matrixes list       | bool  | Put matrixes of each input object into one list (N-panel)                      |
+--------------------------+-------+--------------------------------------------------------------------------------+

See also
--------

* Analyzers-> :ref:`Component Analyzer/Vertices/Normal <VERTICES_NORMAL>`
* Analyzers-> :ref:`Component Analyzer/Vertices/Matrix <VERTICES_MATRIX>`
* Analyzers-> :ref:`Component Analyzer/Edges/Center <EDGES_CENTER>`
* Analyzers-> :ref:`Component Analyzer/Edges/Matrix <EDGES_MATRIX>`
* Analyzers-> :ref:`Component Analyzer/Faces/Center <FACES_CENTER>`
* Analyzers-> :ref:`Component Analyzer/Faces/Normal <FACES_NORMAL>`
* Analyzers-> :ref:`Component Analyzer/Faces/Matrix <FACES_MATRIX>`
* Analyzers-> :ref:`Component Analyzer/Faces/Tangent <FACES_TANGENT>`

Usage
-----

displaying Face normals, for debugging normal directions.

.. image:: https://user-images.githubusercontent.com/14288520/195725890-3878085e-81d9-4aea-936f-be9bf7435d4d.png
  :target: https://user-images.githubusercontent.com/14288520/195725890-3878085e-81d9-4aea-936f-be9bf7435d4d.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* A*SCALAR: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using of corner case of tangent for vertices connected only with one face:

.. image:: https://user-images.githubusercontent.com/14288520/195728391-ee791480-2e5b-4439-a4d9-1020869e4698.png
  :target: https://user-images.githubusercontent.com/14288520/195728391-ee791480-2e5b-4439-a4d9-1020869e4698.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* CROSS: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using matrix output for mesh instancing, looks like work of adaptive polygon node:

.. image:: https://user-images.githubusercontent.com/14288520/195731114-76294da1-c266-427d-a378-51cdf2b586b1.png
  :target: https://user-images.githubusercontent.com/14288520/195731114-76294da1-c266-427d-a378-51cdf2b586b1.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Analyzers-> :doc:`Area </nodes/analyzer/area>`
* MUL: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Easing 0..1 </nodes/number/easing>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix Deform </nodes/matrix/matrix_deform>`
* Matrix-> :doc:`Matrix Apply to Mesh </nodes/matrix/apply_and_join>`
* List->List Struct-> :doc:`List Slice </nodes/list_struct/slice>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`