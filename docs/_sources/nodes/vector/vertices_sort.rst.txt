Vector Sort
===========

Functionality
-------------

This Node sort the sequence of index according to python sort, with different criteria.

Inputs
------

Inputs are vertices lists(vectors, tuple) and polygons/edges as integer lists,
and optional inputs(Vector, matrix and user data)

Parameters
----------

+----------------+-----------------+-------------+----------------------------------------------------+
| Param          | Type            | Default     | Description                                        |
+================+=================+=============+====================================================+
| **Vertices**   | Vector          |             | vertices from nodes generators or lists (in, out)  |
+----------------+-----------------+-------------+----------------------------------------------------+
| **PolyEdge**   | Int             |             | index of polgons or edges     (in, out)            |
+----------------+-----------------+-------------+----------------------------------------------------+
| **Sortmode**   | XYZ, Dist,      | XYZ         | will sort the index according to different criteria|
|                | Axis, Connect,  |             |                                                    |
|                | Auto XYZ,       |             |                                                    |
|                | Auto Direction, |             |                                                    |
|                | Auto Phi / Z,   |             |                                                    |
|                | User            |             |                                                    |
+----------------+-----------------+-------------+----------------------------------------------------+
| **Reverse**    | Boolean         | False       | Reverse the sorting order. Available for           |
|                |                 |             | **Auto Direction** and **Auto Phi / Z** modes.     |
+----------------+-----------------+-------------+----------------------------------------------------+
| **Reverse X**, | Boolean         | False       | Reverse the sorting order when sorting by X, Y or  |
| **Reverse Y**, |                 |             | Z, correspondingly. Available for **XYZ** and      |
| **Reverse Z**  |                 |             | **Auto XYZ** modes only.                           |
+----------------+-----------------+-------------+----------------------------------------------------+
| **Item order** | Int             |             | output the index sequence                          |
+----------------+-----------------+-------------+----------------------------------------------------+
| **Mat**        | Matrix          |             | Matrix for the **Axis** mode.                      |
+----------------+-----------------+-------------+----------------------------------------------------+
| **Base Point** | Vector          |             | Central point for the **Dist** mode.               |
+----------------+-----------------+-------------+----------------------------------------------------+

The sorting modes work as follows:

* **XYZ**. Sort vertices according to X coordinate value, then sort all the
  result according to Y value, then sort all the result according to Z value.
* **Dist**. Sort vertices according to distance from a point specified in the
  **Base Point** input.
* **Axis**.
* **Connect**. Sort vertices according to the order in which they are connected by edges.
* **Auto XYZ**. Automatically detect a plane where all vertices are lying (or a
  plane most similar to that). Then sort vertices in the reference frame of
  that plane: first along X (which is some arbitrary direction along the
  plane), then, if there are some points with the same X - sort them along Y
  (which is some another direction in the plane, but perpendicular to X), and
  then if there are still points with same X and Y - sort them along Z (i.e.
  along the normal of the plane).
* **Auto Direction**. Automatically detect a straight line along which all
  points are lying (or a line most similar to that). Then sort all vertices
  along that line.
* **Auto Phi / Z**. Automatically detect a plane where all the vertices are
  lying (or a plane most similar to that); also calculate a central point in
  that plane (barycenter of all vertices). Then express all vertices in terms
  of cylindrical coordinates in reference frame of such a plane: Z axis is
  pointing along plane's normal, Phi is going counterclockwise around plane's
  normal. Then sort the vertices: first according to Phi value; then, if there
  are points with the same Phi, sort them according to Z value; and, if there
  are points with the same Phi and Z, sort them according to Rho value
  (distance from central normal).

Outputs
-------

The node will output the Vertices as list of Vectors(tuples), Polys/edges as int
and the sorted list of Vertices.

Example of usage
----------------

Example with an Hilbert 3d node and polyline viewer with Vector sort set to Dist:

.. image:: https://cloud.githubusercontent.com/assets/1275858/24357298/7c3e0f6a-12fd-11e7-9852-0d800ec51742.png

The *Connect* mode it is meant to work with paths. Sorting the vertices along the edges.
The "Search fot limits" option will handle discontinities in the path.

Example used to sort the vertices after the *Mesh Filter* node

.. image:: https://user-images.githubusercontent.com/10011941/35187803-3f88191c-fe2a-11e7-874b-da8cb4ec3751.png

Example after *Subdivide* node to prepare vertices for *Vector Evaluation* node and/or *UV Connection* node

.. image:: https://user-images.githubusercontent.com/10011941/35187937-6352b0c0-fe2d-11e7-864c-a3893f94f6dc.png

link to pull request: https://github.com/nortikin/sverchok/pull/88
