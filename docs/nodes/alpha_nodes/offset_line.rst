Offset line
======

Functionality
-------------

This node works only in XY surface. It takes X and Y coordinate from vectors input. Use ``delete loose`` node before if your input mesh has points without edges. You will receive surface along an input mesh edges with width equal offset value. It is also available to receive outer edges and mask of new and old points.

Inputs
------

This node has the following inputs:

- **Vers** - vertices of objects.
- **Edgs** - polygons of objects.
- **offset** - offset values - available single value per object.

Parameters
----------

All parameters can be given by the node or an external input.
``offset`` only one value per object.

+-----------------+---------------+-------------+-------------------------------------------------------------+
| Param           | Type          | Default     | Description                                                 |
+=================+===============+=============+=============================================================+
| **offset**      | Float         | 0.10        | offset values.                                              |
+-----------------+---------------+-------------+-------------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vers**
- **Faces**
- **OuterEdges** - get outer edges, use together with ``delete loose`` node after. The list of edges is unordered.
- **VersMask** - 0 for new points and 1 for old.

Examples of usage
-----------------

To receive offset from input object from scene:

.. image:: https://user-images.githubusercontent.com/28003269/34199193-5e1281a4-e586-11e7-97b8-f1984facdfcb.png

Using of outer edges:

.. image:: https://user-images.githubusercontent.com/28003269/34199326-dadbf508-e586-11e7-9542-7b7ff4a9521f.png

Using of vertices mask with ``transform select`` node:

.. image:: https://user-images.githubusercontent.com/28003269/34199698-125ed63e-e588-11e7-9e34-83c5eb33cde9.png

Different values for each object:

.. image:: https://user-images.githubusercontent.com/28003269/34286982-97be32ea-e6fd-11e7-9e52-5bbc78b36027.png
