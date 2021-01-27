Extrude edges
=============

Functionality
-------------

You can extrude edges along matrices. Every matrix influence on separate vertex of initial mesh.

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

This node does not have parameters.

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

.. image:: https://cloud.githubusercontent.com/assets/5783432/18603880/8d81f272-7c86-11e6-8514-e241557730b0.png

Extruded circle in XY directions by sinus and cosinus drived by pi*N:

.. image:: https://cloud.githubusercontent.com/assets/5783432/18603878/8d80896e-7c86-11e6-8f4a-8d7024ae597b.png

Matrix input node can make skew in one or another direction:

.. image:: https://cloud.githubusercontent.com/assets/5783432/18603891/9fbcc44e-7c86-11e6-8f43-e48ef1eacd59.png

Matrix input node can also scale extruded edges, so you will get bell:

.. image:: https://cloud.githubusercontent.com/assets/5783432/18603881/8d81e9e4-7c86-11e6-9a77-a9104bd234cc.png

Extrude only top edges of the cube:

.. image:: https://user-images.githubusercontent.com/284644/71553527-c9c3b880-2a32-11ea-8e87-c88bd6be744c.png

Extrude only boundary edges of the plane; this also is an example of FaceData socket usage:

.. image:: https://user-images.githubusercontent.com/284644/71553528-ca5c4f00-2a32-11ea-95c4-80c1d85129f1.png

