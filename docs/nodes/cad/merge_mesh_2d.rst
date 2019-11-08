Merge mesh 2d
=============

.. image:: https://user-images.githubusercontent.com/28003269/68468490-91bda780-0231-11ea-8c7d-c37c6d4f372f.png

Functionality
-------------
This node merging to input meshes in one with finding intersections and providing extra information about faces. 

The node tended to be used for 2D mesh only located on 'XY' surface. 
Actually the node just ignore 'Z' coordinate but old points of resulting mesh will be kept with initial 'Z' coordinate 
and 'Z' coordinate of new points will be equal to zero. 
So for avoiding unexpected result they recommend to use `Vecor Math` node in `component-wise U*V` mode 
before `merge mesh 2D` node.

The node can merge two meshes which are overlapping each other. 
It is goal of this node. But also it is possible to have overlapping inside one of the input meshes or both of them. 
It is also is okay but you should be careful in expectation from `mask index` output.

The node is capable of handling overlapping edges and points 
what can seem obvious that it should be but it was a bit tricky in implementation.
Also the node can create holes in polygons. 
The algorithm will split polygon with holes into some pieces so holes lay on boundary of new pieces.

The node can use information related with faces of initial meshes for assign them to new mesh.

Performance
-----------

The node can handle with heavy meshes but there is important parameter as number of intersections
to which the algorithm is sensitive.

It is probably better to avoid using the node with heavy meshes when most parts of first mesh intersects 
with almost all parts of second one. 

Also overlapping edges can slow down the process. 
It is okay when most edges have several overlapping with each other,but performance can slow down dramatically 
if there is at least one edge which has a lot of overlapping with other edges.

Category
--------

CAD -> Merge mesh 2D

Inputs
------

- **VertsA** - vertices of mesh 1
- **FacesA** - faces of mesh 1
- **VertsB** - vertices of mesh 2
- **FacesD** - faces of mesh 2

Outputs
-------

- **Verts** - vertices of merged mesh
- **Faces** - faces of merged mesh
- **Mask A** - list of 0 and 1 related with `faces` socket output where 1 means that face lays inside mesh A
- **Mask B** - list of 0 and 1 related with `faces` socket output where 1 means that face lays inside mesh B
- **Face Index A** (hidden by default) - list of indexes with range from -1 to infinite related with `faces` socket output where index points to face from mesh A
- **Face Index B** (hidden by default) - list of indexes with range from -1 to infinite related with `faces` socket output where index points to face from mesh B

N panel
-------

+--------------------+-------+--------------------------------------------------------------------------------+
| Parameters         | Type  | Description                                                                    |
+====================+=======+================================================================================+
| Simple mask        | Bool  | Switcher of mask sockets                                                       |
+--------------------+-------+--------------------------------------------------------------------------------+
| Index mask         | Bool  | Switcher of index mask sockets                                                 |
+--------------------+-------+--------------------------------------------------------------------------------+
| Accuracy           | int   | Number of figures of decimal part of a number for comparing float values       |
+--------------------+-------+--------------------------------------------------------------------------------+

**Accuracy** - In most cases there is no need in touching this parameter 
but there is some cases when the node can stuck in error and playing with the parameter can resolve the error. 
This parameter does not have any affect to performance in spite of its name.

Masks usage
-----------

For understanding what sockets maskA and maskB returns imagine merging of two squares. 
Result of merging will be 3 faces. MaskA will show result as on the picture below. 
Zero value means that the face  lays outside of the mesh A and one means inside.

.. image:: https://user-images.githubusercontent.com/28003269/66568416-6dab6f80-eb7a-11e9-81d7-8fe527d52eba.png

This is quite useful information which can be handled by `logic function` node and `list mask (out)` node. 
With this information it is possible to get result close to 2D boolean operation.

.. image:: https://user-images.githubusercontent.com/28003269/66569412-93d20f00-eb7c-11e9-9289-44f586ee334c.gif

`Maskindex` output returns more tricky data so it is hidden by default for not confuse users from start.
The meaning of this output is to set data related with faces from initial mesh to resulting mesh.
For example there are initial meshes A and B which have colors assigned to their faces.

.. image:: https://user-images.githubusercontent.com/28003269/66625625-1521b400-ec06-11e9-8165-4a8047cf564f.png

With `MaskIndexA` output and `List index` node it is possible to assign colors from mesh A to new mesh.

.. image:: https://user-images.githubusercontent.com/28003269/66625966-7f872400-ec07-11e9-8f75-400608661388.png

Also it is possible to assign colors from mesh B. 
But in the example in new mesh there are some faces which does not lays inside mesh B. 
In this case the socket returns -1 value. `List item` node will return last element from list with -1 index. 
But with other nodes it is possible to obtain more interesting results. 
For example it is possible to assign colors from mesh B to new mesh but to faces which does not lays inside mesh B assign colors from mesh A.

.. image:: https://user-images.githubusercontent.com/28003269/66634753-c9c7cf80-ec1e-11e9-9046-17db117ef30e.png

It is possible ti use `Mask` and `IndesMask` simultaneously in this way:

.. image:: https://user-images.githubusercontent.com/28003269/66636848-fe3d8a80-ec22-11e9-8149-d26b259e9e49.gif

There is one more thing which should be known. 
According with the fact that algorithm can handle with overlapping of faces even inside one mesh (A or B) 
`MaskIndex` should returns several values to each face 
but for simplicity it returns only first face from list of overlapping faces inside one mesh (A or B).

Usage
-----
**First of all it is possible just crop some mesh by contours of another:**

.. image:: https://user-images.githubusercontent.com/28003269/66644275-93478000-ec31-11e9-975d-d00276ec1d56.png

**Or in a more complex way:**

.. image:: https://user-images.githubusercontent.com/28003269/66561206-14d3db00-eb6a-11e9-9cf4-9f21ea96e01e.png

.. image:: https://user-images.githubusercontent.com/28003269/66561184-0980af80-eb6a-11e9-9784-52c19ed82185.gif

.. image:: https://user-images.githubusercontent.com/28003269/61456611-92c38400-a977-11e9-8ebd-eeb7115aa08b.png

.. image:: https://user-images.githubusercontent.com/28003269/61456563-76bfe280-a977-11e9-9e57-5f44eda0b4da.jpg

**Just as hole maker:**

.. image:: https://user-images.githubusercontent.com/28003269/63747796-07fc7000-c8b9-11e9-89fa-c36542608885.gif

**Pattern maker:**

.. image:: https://user-images.githubusercontent.com/28003269/64519578-6f78dd80-d305-11e9-8bdc-284c2120ec7b.png

**Create simple meshes:**

.. image:: https://user-images.githubusercontent.com/28003269/61684024-f27baf80-ad28-11e9-9f82-38c4ffef8a7f.png

.. image:: https://user-images.githubusercontent.com/28003269/61684160-7897f600-ad29-11e9-8425-3dddba31d951.gif

**Or creating more complex meshes:**

.. image:: https://user-images.githubusercontent.com/28003269/61510835-a5849a00-aa05-11e9-8c5e-fdbd94859cd9.jpg

.. image:: https://user-images.githubusercontent.com/28003269/61510836-a74e5d80-aa05-11e9-878e-1aeea7a2f440.gif

.. image:: https://user-images.githubusercontent.com/28003269/61652698-9c2b5400-acc9-11e9-9251-2ea21ac5391c.png

.. image:: https://user-images.githubusercontent.com/28003269/61652705-a2b9cb80-acc9-11e9-9c57-41e5f49be523.jpg

.. image:: https://user-images.githubusercontent.com/28003269/63831569-f16d1c00-c97f-11e9-812c-98b448e4963f.jpg

**Creating pixel arts and so on and so forth:**

.. image:: https://user-images.githubusercontent.com/28003269/66258738-d29d4900-e7b9-11e9-9685-b00ab2618b95.png