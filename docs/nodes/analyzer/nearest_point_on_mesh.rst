Nearest Point on Mesh
=====================

Functionality
-------------

Finds the closest point in a specified mesh.

Inputs
------

Vertices, Faces: Base mesh for the search
Points: Points to query
Distance: Maximum query distance (only for Nearest in Range mode)

Parameters
----------

*Mode*:
  - Nearest: Nearest point on the mesh surface
  - Nearest in range: Nearest points on the mesh within a range (one per face)

*Flat Output*: (only in Nearest in Range) Flattens the list of every vertex to have only a list for every inputted list.

*Safe Check*: (in N-Panel) When disabled polygon indices referring to unexisting points will crash Blender. Not performing this check makes node faster

Outputs
-------

*Location*: Position of the closest point in the mesh

*Normal*: mesh normal at closets point

*Index*: Face index of the closest point

*Distance*: Distance from the queried point to the closest point

Examples
--------


.. image:: https://user-images.githubusercontent.com/5783432/30777862-8d369f36-a0cd-11e7-8c8e-a72e7aa8ee7f.png
https://github.com/nortikin/sverchok/files/1326934/bvhtree-overlap_2017_09_23_23_07.zip
