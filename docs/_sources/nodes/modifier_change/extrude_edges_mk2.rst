Extrude Edges
=============

.. image:: https://user-images.githubusercontent.com/14288520/200043893-b45dbc77-971a-439d-9be4-f64dcbde010d.png
  :target: https://user-images.githubusercontent.com/14288520/200043893-b45dbc77-971a-439d-9be4-f64dcbde010d.png

Functionality
-------------

You can extrude edges along matrices. Every matrix influence on separate vertex of initial mesh.

.. image:: https://user-images.githubusercontent.com/14288520/200049153-1522d39b-c89e-41e9-9259-b2a28cf6c8b7.png
  :target: https://user-images.githubusercontent.com/14288520/200049153-1522d39b-c89e-41e9-9259-b2a28cf6c8b7.png

Inputs
------

This node has the following inputs:

- **Vertices**. This input is mandatory.
- **Edges**
- **Faces**
- **EdgeMask**. The mask for edges to be extruded. By default, all edges will
  be extruded. Note that providing this input does not have sense if **Edges**
  input was not provided.
- **FaceData**. List containing an arbitrary data item for each face of input
  mesh. For example, this may be used to provide material indexes of input
  mesh faces. Optional input.
- **Matrices**. Matrices for vertices transformation. This input expects one
  matrix per each extruded vertex.

Parameters
----------

Implementation: (in N-panel) Offers Numpy (Faster) and Bmesh (Legacy. Slower)
List Match: (in N-panel) Chose how list length should be matched

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Faces**
- **NewVertices** - only new vertices
- **NewEdges** - only new edges
- **NewPolys** - only new faces.
- **FaceData**. List containing data items from the **FaceData** input, which
  contains one item for each output mesh face.

Examples of usage
-----------------

Extruded circle in Z direction by sinus, drived by pi*N:

.. image:: https://user-images.githubusercontent.com/14288520/200052169-daf55b93-65a8-4926-9d03-c81f977f9b7f.png
  :target: https://user-images.githubusercontent.com/14288520/200052169-daf55b93-65a8-4926-9d03-c81f977f9b7f.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* SUB, MUL, SINE: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Extruded circle in XY directions by sinus and cosinus drived by pi*N:

.. image:: https://user-images.githubusercontent.com/14288520/200053013-696b830d-9ec8-40c2-8662-1d08027d7c3b.png
  :target: https://user-images.githubusercontent.com/14288520/200053013-696b830d-9ec8-40c2-8662-1d08027d7c3b.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* SUB, MUL, SINCOS: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Matrix input node can make skew in one or another direction:

.. image:: https://user-images.githubusercontent.com/14288520/200053481-4a5d04ae-39bb-4a94-a7dd-51d63a6bac7a.png
  :target: https://user-images.githubusercontent.com/14288520/200053481-4a5d04ae-39bb-4a94-a7dd-51d63a6bac7a.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Matrix-> :doc:`Matrix Input </nodes/matrix/input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Matrix input node can also scale extruded edges, so you will get bell:

.. image:: https://user-images.githubusercontent.com/14288520/200054071-6c774ff2-06ef-421b-945b-f842681eebbe.png
  :target: https://user-images.githubusercontent.com/14288520/200054071-6c774ff2-06ef-421b-945b-f842681eebbe.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Matrix-> :doc:`Matrix Input </nodes/matrix/input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Extrude only top edges of the cube:

.. image:: https://user-images.githubusercontent.com/14288520/200054687-06e9797c-39e3-47e4-9159-f5e45e8a46d8.png
  :target: https://user-images.githubusercontent.com/14288520/200054687-06e9797c-39e3-47e4-9159-f5e45e8a46d8.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Analyzers-> :ref:`Select Mesh Elements (By Normal Direction)<MODE_BY_NORMAL_DIRECTION>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Extrude only boundary edges of the plane; this also is an example of FaceData socket usage:

.. image:: https://user-images.githubusercontent.com/284644/71553528-ca5c4f00-2a32-11ea-95c4-80c1d85129f1.png
  :target: https://user-images.githubusercontent.com/284644/71553528-ca5c4f00-2a32-11ea-95c4-80c1d85129f1.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Analyzer-> :doc:`Mesh Filter </nodes/analyzer/mesh_filter>`
* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Mesh Viewer </nodes/viz/mesh_viewer>`
* BPY Data-> :doc:`Assign Materials List </nodes/object_nodes/assign_materials>`