Dissolve faces 2D
=================

.. image:: https://user-images.githubusercontent.com/28003269/68963034-72a1b580-07ef-11ea-8e69-0d16ec073a18.png

Functionality
-------------

The node takes some mesh determined by faces and face mask which represent selected faces of given mesh and
tries to combine adjacent faces with True values of given mask.

The node can combine not all adjacent faces in case if combining can create disjoint parts
or if new face will consist with point which is used several times.

For example if on the picture below all faces would be combined than holes have been lost.

.. image:: https://user-images.githubusercontent.com/28003269/68931279-a4902900-07a9-11ea-8a22-9d25a9997bf9.png

Also this node have optional extra output sockets which should be switched on on N panel.

Face mask outputs returns modified input mask.

Index mask output gives index of old face for every new faces.
It can help to assign for example colors to mesh with new topology from previous mesh.

Category
--------

modifiers -> modifiers change -> Dissolve faces 2D

Inputs
------

- **Vertices** - vertices
- **Faces** - faces (don't try to plug edges)
- **Face mask** (optionally) - selection mask of input faces like [True, False,...] or [1, 0,...]. If the socket is not linked the node tries to dissolve all input faces.

Outputs
-------

- **Vertices** - vertices
- **Faces** - faces, reduced number
- **Face mask** (optionally) - modified input mask according new topology
- **Index mask** (optionally) - index of old face by which new face was created

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Show face mask (N-panel) | bool  | Enable of showing face mask output socket                                      |
+--------------------------+-------+--------------------------------------------------------------------------------+
| show index mask (N-panel)| bool  | Enable of showing face index mask output socket                                |
+--------------------------+-------+--------------------------------------------------------------------------------+


Usage
-----

Dissolving all faces in some shapes generations:

.. image:: https://user-images.githubusercontent.com/28003269/68960424-9530d000-07e9-11ea-9557-3bdc12670823.png

Inserting face into a mesh and dissolving all faces inside the face:

.. image:: https://user-images.githubusercontent.com/28003269/68959819-46cf0180-07e8-11ea-91ae-f28eaf65f955.png