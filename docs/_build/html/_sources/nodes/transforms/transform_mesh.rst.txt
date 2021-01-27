Transform mesh
==============

.. image:: https://user-images.githubusercontent.com/28003269/73248778-010dbc80-41cd-11ea-90be-a778d398945f.png

Functionality
-------------
The node takes mesh and transform it according parameters. It can move, scale and rotate parts of mesh.
The logic is close how Blender manipulate with mesh itself. Selection elements determines by mask input.

.. image:: https://user-images.githubusercontent.com/28003269/73249068-98730f80-41cd-11ea-8ae9-a939cfbe94de.gif

Category
--------

Transforms -> Transform mesh

Inputs
------

- **Verts** - vertices
- **Edges** - edges (optionally), required if selection mode is `edges`  
- **Faces** - faces (optionally), required if selection mode is `faces`
- **Mask** - bool mask or index mask according mask mode
- **Origin** - available with custom origin mode, custom origins
- **Space direction** - available with custom space mode, custom normal
- **Mask index** - available in index mask mode, indexes of mesh parts
- **Direction** - transform vector, axis for rotation mode
- **Factor** - factor of transform vector, radians for rotation mode

Outputs
-------

- **Verts** - transformed vertices

Parameters
----------

+------------------------------+-------+--------------------------------------------------------------------------------+
| Parameters                   | Type  | Description                                                                    |
+==============================+=======+================================================================================+
| Transform mode               | enum  | Move, scale or rotate                                                          |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Mask mode                    | enum  | Bool mask or index mask                                                        |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Origin mode                  | enum  | Bounding box center, median center, individual center, custom center           |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Space mode                   | enum  | Global, normal, custom                                                         |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Selection mode (mask socket) | enum  | Vertexes, edges, faces                                                         |
+------------------------------+-------+--------------------------------------------------------------------------------+
| Direction mode               | enum  | X, Y, Z or custom direction                                                    |
|  (direction socket)          |       |                                                                                |
+------------------------------+-------+--------------------------------------------------------------------------------+

**Boolean mask and values distribution:**
Boolean mask split mesh into selected and unselected parts.
The node apply only one parameter to all selected mesh.
If multiple parameters such as direction vector are given they distributes between selected elements.
Resulting direction vector is calculated by finding average value from distributed among selected elements parameters.

**Index mask and values distribution:**
Index mask marks different parts of mesh with different indexes.
The node apply properties in this mode only for parts of mesh 
with indexes equal to given indexes via `mask index` socket.

For example: 

given indexes - [1, 3], given parameters - [param1, param2]. 

All parts of mesh masked by 1 will be assigned with param1.

All parts of mesh masked by 3 will be assigned param2.

All other parts will be unchanged.

Examples
--------

Generating and moving lines on mesh level:

.. image:: https://user-images.githubusercontent.com/28003269/73343086-616a3000-4299-11ea-8b7b-67110bf72fa8.png

Moving disjoint parts =):

.. image:: https://user-images.githubusercontent.com/28003269/73347577-469bb980-42a1-11ea-889b-b4d87c754f2d.gif

.. image:: https://user-images.githubusercontent.com/28003269/73347608-53201200-42a1-11ea-96bb-358ada087da4.png

randomly scaled faces:

.. image:: https://user-images.githubusercontent.com/28003269/73352227-202e4c00-42aa-11ea-81ed-7d600ef1ce96.png

Randomly scaled loops of torus:

.. image:: https://user-images.githubusercontent.com/28003269/73356416-bfa40c80-42b3-11ea-95b5-43e7bab2918d.png

Flatten monkey by nearby point:

.. image:: https://user-images.githubusercontent.com/28003269/73169759-3905f880-4116-11ea-9c8d-d565371ff7a9.png