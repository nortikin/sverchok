Plane Intersection
==================

Functionality
-------------

The node is designed to get the intersection line between two theoretical planes.

Each plane is defined by one point in the plane and plane's normal.


Inputs / Parameters
-------------------


+------------------+-------------+----------------------------------------------------------------------+
| Param            | Type        | Description                                                          |  
+==================+=============+======================================================================+
| **Location A**   | Vertices    | One point of the plane A                                             | 
+------------------+-------------+----------------------------------------------------------------------+
| **Normal A**     | Vertices    | Normal of the plane A                                                |
+------------------+-------------+----------------------------------------------------------------------+
| **Location B**   | Vertices    | One point of the plane B                                             | 
+------------------+-------------+----------------------------------------------------------------------+
| **Normal B**     | Vertices    | Normal of the plane B                                                |
+------------------+-------------+----------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching inside groups (level 2)


Outputs
-------

**Intersect**: Returns True if the planes are not parallel.

**Origin**: Origin of the line. If planes are parallel returns the origin of plane A

**Direction**: Direction of the line. If planes are parallel returns the normal of both planes

Example of usage
----------------

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_plane_plane/sverchok_intersect_plane_plane_example1.png
  :alt: sverchok_intersect_plane_plane_example1.png


.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_plane_plane/sverchok_intersect_plane_plane_example.png
  :alt: sverchok_intersect_plane_plane_example1.png
