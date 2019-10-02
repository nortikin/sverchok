Bounding Box
============

Functionality
-------------

Generates a special ordered *bounding box* from incoming Vertices.

Inputs
------

**Vertices**, or a nested list of vertices that represent separate objects.

Parameters
----------

Min, Max and Size: Chose which outputs you want the node to display

Outputs
-------

+----------+-----------+----------------------------------------------------------------------------+
| Output   | Type      | Description                                                                |
+==========+===========+============================================================================+
| Vertices | Vectors   | One or more sets of Bounding Box vertices.                                 |
+----------+-----------+----------------------------------------------------------------------------+
| Edges    | Key Lists | One or more sets of Edges corresponding to the Vertices of the same index. |
+----------+-----------+----------------------------------------------------------------------------+
| Mean     | Vectors   | Arithmetic averages of the incoming sets of vertices                       |
+----------+-----------+----------------------------------------------------------------------------+
| Center   | Matrix    | Represents the *Center* of the bounding box; the average of its vertices.  |
|          |           | The scale of the matrix would make a box with size of 1 unit to match the  |
|          |           | size the desired bounding box                                              |
+----------+-----------+----------------------------------------------------------------------------+
| Min X    | Scalar    | Minimum value on the X axis                                                |
+----------+-----------+----------------------------------------------------------------------------+
| Min Y    | Scalar    | Minimum value on the Y axis                                                |
+----------+-----------+----------------------------------------------------------------------------+
| Min Z    | Scalar    | Minimum value on the Z axis                                                |
+----------+-----------+----------------------------------------------------------------------------+
| Max X    | Scalar    | Maximum value on the X axis                                                |
+----------+-----------+----------------------------------------------------------------------------+
| Max Y    | Scalar    | Maximum value on the Y axis                                                |
+----------+-----------+----------------------------------------------------------------------------+
| Max Z    | Scalar    | Maximum value on the Z axis                                                |
+----------+-----------+----------------------------------------------------------------------------+
| Size X   | Scalar    | Size on the X axis                                                         |
+----------+-----------+----------------------------------------------------------------------------+
| Size Y   | Scalar    | Size on the Y axis                                                         |
+----------+-----------+----------------------------------------------------------------------------+
| Size Z   | Scalar    | Size on the Z axis                                                         |
+----------+-----------+----------------------------------------------------------------------------+



Examples
--------

*Mean: Average of incoming set of Vertices*

.. image:: https://cloud.githubusercontent.com/assets/619340/4186539/def83614-3761-11e4-9cb4-4f7d8a8608bb.PNG
  :alt: BBox_Mean1.PNG

*Center: Average of the Bounding Box*

.. image:: https://cloud.githubusercontent.com/assets/619340/4186538/def29d62-3761-11e4-8069-b9544e2ad62a.PNG
  :alt: BBox_Center3.PNG

Notes
-----

GitHub issue tracker `discussion about this node <https://github.com/nortikin/sverchok/issues/161>`_
