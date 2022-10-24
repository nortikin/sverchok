Plane Intersection
==================

.. image:: https://user-images.githubusercontent.com/14288520/196056532-de22a881-5d36-4a6d-bc19-e80b5ae4173e.png
  :target: https://user-images.githubusercontent.com/14288520/196056532-de22a881-5d36-4a6d-bc19-e80b5ae4173e.png

.. image:: https://user-images.githubusercontent.com/14288520/196057909-2604f799-3136-448f-9db8-457a9f554b4d.png
  :target: https://user-images.githubusercontent.com/14288520/196057909-2604f799-3136-448f-9db8-457a9f554b4d.png

.. image:: https://user-images.githubusercontent.com/14288520/196058228-3507e0fa-e8c0-4cc2-af67-ac96a71df9ce.png
  :target: https://user-images.githubusercontent.com/14288520/196058228-3507e0fa-e8c0-4cc2-af67-ac96a71df9ce.png

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

* **Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)
* **Match List Local**: Define how list with different lengths should be matched. Refers to the matching inside groups (level 2)


Outputs
-------

* **Intersect**: Returns True if the planes are not parallel.
* **Origin**: Origin of the line. If planes are parallel returns the origin of plane A
* **Direction**: Direction of the line. If planes are parallel returns the normal of both planes

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/196059332-d1fffc72-e144-4c96-b220-6ea9fca75b89.png
  :target: https://user-images.githubusercontent.com/14288520/196059332-d1fffc72-e144-4c96-b220-6ea9fca75b89.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Analyzers-> :doc:`Origins </nodes/analyzer/origins>`
* Transform-> :doc:`Matrix Apply (verts) </nodes/transforms/apply>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

---------

.. image:: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_plane_plane/sverchok_intersect_plane_plane_example.png
  :target: https://github.com/vicdoval/sverchok/raw/docs_images/images_for_docs/analyzer/intersect_plane_plane/sverchok_intersect_plane_plane_example.png
  :alt: sverchok_intersect_plane_plane_example1.png
