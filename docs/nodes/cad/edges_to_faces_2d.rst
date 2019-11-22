Edges to faces 2D
=================

.. image:: https://user-images.githubusercontent.com/28003269/67938049-30218b80-fbe8-11e9-9da7-c65df2de733e.png

Functionality
-------------
The node try create faces from given edges in 2D mode. 
It include some clever features as find self intersections of edge net and detection polygons with holes and 
convert them in proper condition for visualization nodes.

Prefix 2D means that the node expects from input any kind of flatten mesh
but it does not mean that the mesh should only lay on XY surface.
Input mesh can below or above XY surface or even can be tilted relative one.

There some corner case when work of the node can be broken. First try to change `accuracy` parameter in N panel. 
Also it is possible that one of new polygons has self intersection in its points. 
The node is not designed at this stage for handling such case.

.. image:: https://user-images.githubusercontent.com/28003269/67850794-87f5bf00-fb22-11e9-8e10-8ab61ccf810a.png

Category
--------

CAD -> Edges to faces 2D

Inputs
------

- **Vertices** - vertices of edge net
- **Edges** - edges (don't try to plug faces)

Outputs
-------

- **Vertices** - vertices, can produce new vertices in intersection mode
- **Faces** - faces, also new edges can be added for showing holes

Parameters
----------

+--------------------+-------+--------------------------------------------------------------------------------+
| Parameters         | Type  | Description                                                                    |
+====================+=======+================================================================================+
| Self intersect     | bool  | Searching self intersections                                                   |
+--------------------+-------+--------------------------------------------------------------------------------+
| Fill holes         | bool  | Create faces for detected holes                                                |
+--------------------+-------+--------------------------------------------------------------------------------+
| Accuracy (N-panel) | int   | Number of figures of decimal part of a number for comparing float values       |
+--------------------+-------+--------------------------------------------------------------------------------+

**Self intersection** - If it is quite reasonably clear what this option do with intersection it can be not clear
that this option also is responsible for finding holes. 
If there is face inside another face without intersection with the face 
the finding intersection algorithm will consider this face as a hole. 
If intersection is off the face will be recognize as independent one.

**Fill holes** - If this option is on it views all generated faces. 
If it is off the node works in more interesting way. 
If hole detected the face of the hole is not going to be created. 
If hole also has a hole second hole will be filled with face. 
This algorithm will be repeated recursively over all nested holes.

**Accuracy** - In most cases there is no need in touching this parameter
but there is some cases when the node can stuck in error and playing with the parameter can resolve the error.
This parameter does not have any affect to performance in spite of its name.

Dissolving tail edges algorithm
-------------------------------

It also worth to light such specific behaviour of the node as dissolving tail edges. 
Tail edge is an edge from both side of which there is the same face. 
Actually, polygons with such tail edges can't be viewed without extra preparations. 
The node just ignore such edges for simplicity of algorithm. 
After such deleting joined parts of mesh can become disjoint and inner parts of mesh can become holes.

In the example below there are initial mesh with tail edges and result of the node. 
All tail edges are gone but some new edges was created. 
New edges creates for viewing faces with holes as if the faces was without holes.

.. image:: https://user-images.githubusercontent.com/28003269/67653172-a3fe3280-f961-11e9-91bf-93c0425707fa.png

**One more example of work principles:**

.. image:: https://user-images.githubusercontent.com/28003269/67849943-e0c45800-fb20-11e9-84b0-2b45624b90ca.gif

**Example of work of filling holes:**

.. image:: https://user-images.githubusercontent.com/28003269/67938067-3879c680-fbe8-11e9-87ec-a882441d3db9.gif

Usage
-----

**Intersection of generated edges randomly:**

.. image:: https://user-images.githubusercontent.com/28003269/67630013-d3496c80-f899-11e9-8bad-77f9bc196eab.gif

.. image:: https://user-images.githubusercontent.com/28003269/67947987-302c8600-fbfe-11e9-8c0e-a8c9ddda90d1.png

**Work of contour 2D node and this node in tandem:**

.. image:: https://user-images.githubusercontent.com/28003269/67938552-26e4ee80-fbe9-11e9-9db7-f6cb8bdc5b18.png

**Creating of some patterns:**

.. image:: https://user-images.githubusercontent.com/28003269/67940398-028b1100-fbed-11e9-8bcc-ac496721e1f5.gif