Bounding Box
============

Functionality
-------------

Generates a special ordered *bounding box* from incoming Vertices. 

Inputs
------

Vertices, or a nested list of vertices that represent separate objects.

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
| Center   | Matrix    | Represents the *Center* of the bounding box; the average of its vertices   |
+----------+-----------+----------------------------------------------------------------------------+



Examples
--------

*Mean: Average of incoming set of Vertices*

.. image:: BBox_Mean1.PNG

*Center: Average of the Bounding Box*

.. image:: BBox_Center3.PNG

Notes
-----

GitHub issue tracker `discussion about this node <https://github.com/nortikin/sverchok/issues/161>`_