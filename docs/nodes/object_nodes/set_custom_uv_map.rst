Set custom UV map
=================

.. image:: https://user-images.githubusercontent.com/28003269/72145465-04730c80-33b4-11ea-830a-1ce9ba114b7d.png

Functionality
-------------
The node creates custom UV layer and apply given uv coordinates to given Blender mesh object.
For usability the node has matrix input socket but the same can be done applying the same matrix 
to input UV coordinates outside of the node.
UV coordinates should be prepared by other nodes.

Category
--------

BPY Data -> Set custom UV map

Inputs
------

- **Objects** - Blender mesh objects
- **UV verts** - just usual vertices (3D dimensional )
- **UV faces** - just usual face, each face can be disjoint from each other
- **Matrix** - optional, fro UV transformation

Outputs
-------

- **Objects** - Blender mesh objects

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| Name of UV layer         | str   | SVMap by default                                                               |
+--------------------------+-------+--------------------------------------------------------------------------------+

Usage
-----

First of all own mesh of a mesh can be used as UV data. In this case flat projection will be get:

.. image:: https://user-images.githubusercontent.com/28003269/71992782-68c88b80-324f-11ea-8cdc-0312d2dac19e.png

This is analog of this set of nodes in material editor:

.. image:: https://user-images.githubusercontent.com/28003269/72155099-c41f8880-33cb-11ea-8315-909d3d76f80e.png

If input mesh has only quad faces it is possible to use plane generator node for UV mapping:

.. image:: https://user-images.githubusercontent.com/28003269/72155281-33957800-33cc-11ea-8a4e-5bc7931935f1.png

Some tricky way of unwrapping mesh with arbitrary number of edges in faces:

.. image:: https://user-images.githubusercontent.com/28003269/72155683-13b28400-33cd-11ea-88ae-a87dfd05b928.png

And of using special for unwrapping nodes:

.. image:: https://user-images.githubusercontent.com/28003269/71994775-c90cfc80-3252-11ea-835f-1b0ebbe449b7.png
