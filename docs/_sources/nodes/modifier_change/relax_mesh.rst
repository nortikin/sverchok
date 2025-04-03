Relax Mesh
==========

.. image:: https://user-images.githubusercontent.com/14288520/198748668-f00fe217-fdb8-4fca-bb91-a3077ceb5e27.png
  :target: https://user-images.githubusercontent.com/14288520/198748668-f00fe217-fdb8-4fca-bb91-a3077ceb5e27.png

Functionality
-------------

This node moves vertices of the input mesh, in order to make it more "relaxed",
i.e. for mesh elements to have more even distribution in some sense. There are
several algorithms supported, each of which has different definition of what "relaxed" is:

* Lloyd-based algorithm. This is created after well-known Lloyd algorithm. For
  each vertex, find centers of all incident faces, and then find the average of
  those points; this will be the new location of the vertex. Effectively, this
  algorithm tries to make each face as close to circle as possible. This
  algorithm shows it's best for meshes that consist of Tris.
* Edge lengths. Scale each edge up or down, trying to make all edges of the
  same length. Target edge length can be minimum, maximum or average of all
  lengths of edges of the source mesh.
* Face areas. Scale each face up or down, trying to make all faces of the same
  area. Target face area can be minimum, maximum or average of all areas of
  faces of the source mes.

These algorithms can change the overall shape of the mesh a lot. In order to
try to preserve original shape of the mesh at least partially, the following
methods are supported:

* "Linear" method is supported for Lloyd algorithm only. When the algorithm has
  found the new location of the vertex, put it at the same distance from the
  plane where centers of incident faces lie, as the original vertex was. This
  method can be slow for large meshes.
* "Tangent": move vertices along tangent planes of original vertexes only (i.e.
  perpendicular to vertex normal).
* "BVH": use BVH tree to find the nearest point to the newly calculated vertex
  on the original mesh.

Inputs
------

This node has the following inputs:

* **Vertices**. Vertices of the original mesh. This input is mandatory.
* **Edges**. Edges of the original mesh.
* **Faces**. Faces of the original mesh. This input is mandatory.
* **VertMask**. Mask defining which vertices are to be moved. By default, all vertices can be moved.
* **Iterations**. Number of iterations of algorithm. Default value is 1.
* **Factor**. This input is available for **Edge Length** and **Face Area**
  algorithms. Coefficient to be used at each iteration of the algorithm.
  Possible values are between 0 and 1. The default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Algorithm**. Relaxation algorithm to be used. The available options are
  **Lloyd**, **Edge Length** and **Face Area**. The default option is
  **Lloyd**.
* **Target**. This parameter is available for **Edge Length** and **Face Area**
  algorithms. This defines which value of edge length or face area is to be
  used as the target value for the algorithm. The available options are
  **Average**, **Minimum** and **Maximum**. The default option is **Average**.
* **Preserve shape**. This defines the method to be used in order to preserve
  the shape of the original mesh at least partially. The available options are
  **Do not use**, **Linear** (for Lloyd algorithm only), **Tangent** and
  **BVH**. The default option is **Do not use**.
* **Skip bounds**. If checked, the node will not move boundary vertexes of the
  original mesh. Checked by default.
* **X**, **Y**, **Z**. These parameters define the coordinate axes along which
  it is allowed to move vertices. By default, all three parameters are checked,
  which means the node can move vertices in any direction.

Outputs
-------

This node has the following output:

* **Vertices**. Vertices of the relaxed mesh.

The node does not modify edges or faces of the original mesh, it only moves the vertexes.

Example of Usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/103518798-323f4400-4e96-11eb-8980-39cbac4a5a40.png

