KDT Closest Edges
=================

*Alias: KDTree Edges*

Functionality
-------------

On each update it takes an incoming pool of Vertices and places them in a K-dimensional Tree.
It will return the Edges it can make between those vertices pairs that satisfy the constraints
imposed by the 4 parameters.

Inputs
------

- Verts, a pool of vertices to iterate through

Parameters
----------

+------------+-------+-----------------------------------------------------------+
| Parameter  | Type  | Description                                               |
+============+=======+===========================================================+
| mindist    | float | Minimum Distance to accept a pair                         |
+------------+-------+-----------------------------------------------------------+
| maxdist    | float | Maximum Distance to accept a pair                         |
+------------+-------+-----------------------------------------------------------+
| maxNum     | int   | Max number of edges to associate with the incoming vertex |
+------------+-------+-----------------------------------------------------------+
| Skip       | int   | Skip first n found matches if possible                    |
+------------+-------+-----------------------------------------------------------+

Fast Mode
---------

This mode requires Scipy dependency. It can be from 3 to 10 times faster but lacks of 'maxNum' and 'Skip' properties

.. image:: https://user-images.githubusercontent.com/10011941/101905604-017e2e80-3bb8-11eb-894d-67a3c6c51e93.png


Max Queries Mode
----------------

This mode requires Scipy dependency. In this mode the maxNum property is used to determine how many points will be verified so it will produce less connections that the complete mode

.. image:: https://user-images.githubusercontent.com/10011941/101905663-15c22b80-3bb8-11eb-8625-4e48085a2dfe.png

No Skip Mode
------------

This mode requires Scipy dependency. This is similar to the existing mode but the way the maximum connections is coded produces different results sorting the filter by minimum vertex index

.. image:: https://user-images.githubusercontent.com/10011941/101906167-d3e5b500-3bb8-11eb-9b71-e11b3fb5c316.png



Outputs
-------

- Edges, which can connect the pool of incoming Verts to each other.
