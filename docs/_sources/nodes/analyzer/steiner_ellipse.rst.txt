Steiner Ellipse
===============

Functionality
-------------

This node can generate either Steiner inellipse_ (inscribed ellipse) or Steiner
ellipse (circumellipse_) for each triangular face of the input mesh. For non-tri
faces, the node will either skip them or give an error, depending on a setting.

.. _inellipse: https://en.wikipedia.org/wiki/Steiner_inellipse
.. _circumellipse: https://en.wikipedia.org/wiki/Steiner_ellipse

Main properties of the Steiner inellipse are:

* It touches each side of the triangle in the midpoint of that side;
* The center of the ellipse is the centroid (barycenter) of the triangle.

Main properties of the Steiner circumellipse are:

* It touches the triangle in it's vertices;
* The center of the ellipse is the centroid (barycenter) of the triangle.

Inputs
------

This node has the following inputs:

- **Vertices**. The vertices of the input mesh. This input is mandatory.
- **Faces**. The faces of the input mesh. This input is mandatory.

Parameters
-----------

This node has the following parameters:

- **Mode**. Defines which ellipses should be generated. The available modes are:

  - **Inellipse**. Generate Steiner inellipses (inscribed ellipses). This is the default mode.
  - **Circumellipse**. Generate Steiner circumellipses.

- **On non-tri faces**. Defines what the node should do if it encounters a
  non-triangular face. There are following options available:

   - **Skip**. Just skip such faces - do not generate inscribed circles for them.
   - **Error**. Stop processing and give an error (turn the node red).

   The default option is **Skip**. This parameter is available in the N panel only.

Outputs
-------

This node has the following outputs:

- **Center**. Centers of the ellipses.
- **F1**, **F2**. Focal points of the ellipses.
- **SemiMajorAxis**. Lengths of semi-major axes of the ellipses.
- **SemiMinorAxis**. Lengths of semi-minor axes of the ellipses.
- **C**. Distances from the center of ellipse to it's focal points.
- **Eccentricity**. Eccentricity values of the ellipses.
- **Normal**. Normals of the planes where ellipses lie; i.e. face normals.
- **Matrix**. For each ellipse, this contains a matrix, Z axis of which points
  along face normal, and the translation component equals to the center of the
  ellipse. This output can be used to actually place ellipses at their places.

Examples of usage
-----------------

Inscribed ellipses for Delaunay triangulation of some random points:

.. image:: https://user-images.githubusercontent.com/284644/75094441-ea306f00-55ac-11ea-919d-0d2851037c1e.png

Inscribed ellipses for triangulated Suzanne:

.. image:: https://user-images.githubusercontent.com/284644/75094444-eb619c00-55ac-11ea-82da-056a0232a89f.png

Circumellipse of some random triangle, with it's center and focal points indicated:

.. image:: https://user-images.githubusercontent.com/284644/75094701-9d9a6300-55af-11ea-899f-11b5060286c7.png

