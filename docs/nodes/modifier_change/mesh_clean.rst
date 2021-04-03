Mesh Clean
==========

Functionality
-------------

Cleans input mesh by removing doubled, unreferenced or bad formed elements.

Options
-------

**Unreferenced Edges**: Remove the edges that point to un-existing vertices.

**Unreferenced Faces**: Remove the faces that point to un-existing vertices.

**Duplicated Edges**: Remove duplicated edges. Note that edges as (0,1) and (1,0) will be considered identical.

**Duplicated Faces**: Remove duplicated faces. Note that faces as (0,1,2,3) and (1,0,3,2) will be considered identical.

**Degenerated Edges**: Check for edges with repeated indices and remove them.

**Degenerated Faces**: Check for repeated indices on every face and remove them, if it has less than 3 vertices then the face will be removed

**Unused Vertices**: Removes the vertices not used to create any edge or face.


Inputs
------

Vertices, Edges and Faces

Outputs
-------

Vertices, Edges and Faces: Cleaned Mesh Data

Removed Vertices Idx: the index of the removed vertices

Removed Edges Idx: the index of the removed edges

Removed Faces Idx: the index of the removed faces

Examples
--------

.. image:: https://user-images.githubusercontent.com/10011941/113458705-739eab80-9413-11eb-8605-03d4be6b33a9.png
