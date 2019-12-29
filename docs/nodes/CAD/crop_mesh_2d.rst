Crop mesh 2D
============

.. image:: https://user-images.githubusercontent.com/28003269/71086774-1b0eb500-21b4-11ea-91c0-37c932309d0a.png

Functionality
-------------
The node takes two meshes determined by faces find them intersection and dependently of mode
show either overlapping each other faces or faces of first mesh which has not overlapping.

Differently to say crop mesh can crete holes in base mesh in outer mode or
base mesh can be insert in crop mesh in inner mode.

The node can take edges for base mesh and crop them according the same logic. Crop mesh always should have faces.

Prefix 2D means that the node expects from input any kind of flatten mesh
but it does not mean that the mesh should only lay on XY surface.
Input mesh can below or above XY surface or even can be tilted relative one.

Also this node have optional extra output socket of face index mash which should be switched on on N panel.
This output gives index of old face for every new faces.
It can help to assign for example colors to mesh with new topology from previous mesh.
It available only ind faces mode.

**Warning:**

This node is not 100 % robust. Some corner cases can knock it out. If you get an error or unexpected result check:

- did not you try to plug edges instead of faces and vise versa.
- try to change accuracy parameter on N panel.

Blender mode
------------

This mode is using internal Blender function so it is faster but can crash Blender. 
Also it works only with faces at this moment.

Category
--------

CAD -> crop mesh 2d

Inputs
------

- **Vertices** - vertices of base mesh
- **Faces** or **Edges** - faces of base mesh (don't try to plug edges)
- **Vertices Crop** - vertices of cropping mesh
- **Faces Crop** - faces of cropping mesh (don't try to plug edges)

Outputs
-------

- **Vertices** - vertices, can produce new vertices
- **Faces** or **Edges** - faces, also new edges can be added for showing holes
- **Face index** (face mode only) - index of old face by which new face was created

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Faces                    | bool  | Enable faces mode of input mesh, so faces should be plugged into input socket  |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Edges                    | bool  | Enable edges mode of input mesh, so edges should be plugged into input socket  |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Inner                    | bool  | Enable inner mode fro inserting mesh into crop mesh                            |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Outer                    | bool  | Enable outer mode for creating holes in base mesh                              |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Accuracy (N-panel)       | int   | Number of figures of decimal part of a number for comparing float values       |
+--------------------------+-------+--------------------------------------------------------------------------------+

**Accuracy** - In most cases there is no need in touching this parameter
but there is some cases when the node can stuck in error and playing with the parameter can resolve the error.
This parameter does not have any affect to performance in spite of its name.

Usage
-----

Creating holes:

.. image:: https://user-images.githubusercontent.com/28003269/68539557-2eea1e80-039f-11ea-91d2-aabb4399a9db.png

Fit mesh inside mesh:

.. image:: https://user-images.githubusercontent.com/28003269/68539501-95227180-039e-11ea-9836-404d7687cd14.png

Crop Voronoi diagram by some shape:

.. image:: https://user-images.githubusercontent.com/28003269/68539337-5dfe9100-039b-11ea-9811-1a1733a447c8.png

Creating something like sewer grate:

.. image:: https://user-images.githubusercontent.com/28003269/68532980-8e174700-033d-11ea-8134-8da6b13c8121.png

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/68381924-1f36c400-016c-11ea-9984-07c4a27688d1.png
