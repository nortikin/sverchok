Crop mesh 2D
============

.. image:: https://user-images.githubusercontent.com/28003269/68309560-0bd21d00-00c8-11ea-94cf-8c6e523b6128.png

Functionality
-------------
The node takes two meshes determined by faces find them intersection and dependently of mode 
show either overlapping each other faces or faces of first mesh which has not overlapping.

Differently to say crop mesh can crete holes in base mesh in outer mode or 
base mesh can be insert in crop mesh in inner mode.

Also this node have optional extra output socket of face index mash which should be switched on on N panel.
This output gives index of old face for every new faces.
It can help to assign for example colors to mesh with new topology from previous mesh.

**Warning:**

This node is not 100 % robust. Some corner cases can knock it out. If you get an error or unexpected result check:

- did not you try to plug edges instead of faces.
- try to change accuracy parameter on N panel.

Category
--------

CAD -> crop mesh 2d

Inputs
------

- **Vertices** - vertices of base mesh
- **Faces** - faces of base mesh (don't try to plug edges)
- **Vertices Crop** - vertices of cropping mesh
- **Faces Crop** - faces of cropping mesh (don't try to plug edges)

Outputs
-------

- **Vertices** - vertices, can produce new vertices
- **Faces** - faces, also new edges can be added for showing holes
- **Face index** (optionally) - index of old face by which new face was created 

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Inner                    | bool  | Enable inner mode fro inserting mesh into crop mesh                            |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Outer                    | bool  | Enable outer mode for creating holes in base mesh                              |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Show face mask (N-panel) | bool  | Enable of showing face index mask output socket                                |
+--------------------------+-------+--------------------------------------------------------------------------------+
| Accuracy (N-panel)       | int   | Number of figures of decimal part of a number for comparing float values       |
+--------------------------+-------+--------------------------------------------------------------------------------+

**Accuracy** - In most cases there is no need in touching this parameter
but there is some cases when the node can stuck in error and playing with the parameter can resolve the error.
This parameter does not have any affect to performance in spite of its name.

Usage
-----

Creating holes:

.. image:: https://user-images.githubusercontent.com/28003269/68450210-a5521980-0203-11ea-87a1-19f52129f91b.png

Fit mesh inside mesh:

.. image:: https://user-images.githubusercontent.com/28003269/68450333-201b3480-0204-11ea-9faa-493ec884f774.png

Examples
--------

.. image:: https://user-images.githubusercontent.com/28003269/68381924-1f36c400-016c-11ea-9984-07c4a27688d1.png