Voronoi Field
=============

Functionality
-------------

This node generates a Vector Field and a Scalar Field, which are defined
according to the Voronoi diagram for the specified set of points ("voronoi
sites"):

* The scalar field value for some point is calculated as the difference between
  distances from this point to two nearest Voronoi sites;
* The vector field vector for some point points from this point towards the
  nearest Voronoi site. The absolute value of this vector is equal to the value
  of Voronoi scalar field in this point.

So, the set of points (planar areas), where scalar field equals to zero, is
exactly the Voronoi diagram for the specified set of sites.

Inputs
------

This node has the following input:

* **Vertices**. The set of points (sites) to form Voronoi field for. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **SField**. Voronoi scalar field.
* **VField**. Voronoi vector field.

Examples of usage
-----------------

Use Voronoi scalar field of three points (marked with red spheres) to scale blue spheres:

.. image:: https://user-images.githubusercontent.com/284644/79604012-cf8afa00-8106-11ea-9283-0856cd0a0a6c.png

Visualize the lines of corresponding vector field:

.. image:: https://user-images.githubusercontent.com/284644/79604015-d0bc2700-8106-11ea-9f5d-621fdc900fcb.png

Apply the vector field to some box:

.. image:: https://user-images.githubusercontent.com/284644/79604016-d0bc2700-8106-11ea-8863-dbb9af6ab8b3.png

