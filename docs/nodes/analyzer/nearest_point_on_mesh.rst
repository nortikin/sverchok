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

Used as skin-wrap modifier:

.. image:: https://user-images.githubusercontent.com/10011941/111774583-f3733480-88af-11eb-9559-78392166b00c.png


Determine which polygons are nearer than a distance:

.. image:: https://user-images.githubusercontent.com/10011941/111812010-f255fd80-88d7-11eb-8f48-de67716dd93a.png


Placing objects on mesh:

.. image:: https://user-images.githubusercontent.com/10011941/111810852-bf5f3a00-88d6-11eb-9cff-eb2a6c18a01a.png
