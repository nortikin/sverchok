Apply Matrix to Mesh
====================

Functionality
-------------

Applies a Transform Matrix to a list or nested lists of vertices, edges and faces. If several matrices are provided on the input, then this node will produce several meshes.

**Note**. Unless there is further processing going on which explicitly require the duplicated topology, then letting the ``Viewer Draw`` or ``BMesh Viewer`` nodes automatically repeat the index lists for the edges and faces is slightly more efficient than use of this node.


Inputs
------

This node has the following inputs:

- **Vertices**. Represents vertices or intermediate vectors used for further vector math.
- **Edges**
- **Faces**
- **Matrices**. One or more, never empty.

Parameters
----------

This node has the following parameter:

**Join**. If set, then this node will join output meshes into one mesh, the same way as ``Mesh Join`` node does.
Otherwise, if N matrices are provided at the input, this node will produce N lists of vertices, N lists of edges and N lists of faces.

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: 'NumPy' or 'Python'. As a general rule in this node the Numpy implementation will be faster if any input is a NumPy array or you want to get NumPy arrays from the outputs. If the surrounding nodes are using python list the performance of both implementations will depend on many factors. With a light geometry but many matrices the Python implementation will be faster, as heavier gets the input geometry and less the matrices number the NumPy implementation will start being a better choice. Also if the incoming topology of polygons is regular the NumPy implementation will increase its performance while the Python implementation will not be affected by that parameter.

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Polygons in the NumPy implementation

Outputs
-------

This node has the following outputs:

- **Vertices**.  Nested list of vectors / vertices, matching the number nested incoming *matrices*.
- **Edges**. Input edges list, repeated the number of incoming matrices. Empty if corresponding input is empty.
- **Faces**. Input faces list, repeated the number of incoming matrices. Empty if corresponding input is empty.

Examples
--------

.. image:: https://cloud.githubusercontent.com/assets/284644/6096652/ac13659e-afbf-11e4-83c9-e13b75c0e346.png

.. image:: https://cloud.githubusercontent.com/assets/284644/6096654/b300fbfa-afbf-11e4-901b-1361a44238c2.png
