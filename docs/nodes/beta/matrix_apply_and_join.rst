Apply Matrix to Mesh
====================

Functionality
-------------

Applies a Transform Matrix to a list or nested lists of vertices, edges and faces. If several matrices are provided on the input, then this node will produce several meshes.


Inputs
------

This node has the following inputs:

- **Vertices**. Represents vertices or intermediate vectors used for further vector math.
- **Edges**
- **Faces**
- **Matrices**. One or more, never empty.

Outputs
-------

This node has the following outputs:

- **Vertices**.  Nested list of vectors / vertices, matching the number nested incoming *matrices*.
- **Edges**. Input edges list, repeated the number of incoming matrices. Empty if corresponding input is empty.
- **Faces**. Input faces list, repeated the number of incoming matrices. Empty if corresponding input is empty.

So if N matrices are provided at the input, then this node will produce N lists of vertices, N lists of edges and N lists of faces.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/284644/6096652/ac13659e-afbf-11e4-83c9-e13b75c0e346.png

.. image:: https://cloud.githubusercontent.com/assets/284644/6096654/b300fbfa-afbf-11e4-901b-1361a44238c2.png

