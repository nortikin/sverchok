Cross Section
=============

.. image:: https://user-images.githubusercontent.com/14288520/198750762-7dab4e74-e87e-4d72-b25b-90e0814c327b.png
  :target: https://user-images.githubusercontent.com/14288520/198750762-7dab4e74-e87e-4d72-b25b-90e0814c327b.png

Functionality
-------------

Sect object with blender operator to edges/polygons (F or Alt+F cases). In some cases work better than new bisect node.

.. image:: https://user-images.githubusercontent.com/14288520/198750770-d8a0e626-91c8-44ba-ab39-8fa26a932ecf.png
  :target: https://user-images.githubusercontent.com/14288520/198750770-d8a0e626-91c8-44ba-ab39-8fa26a932ecf.png

Inputs
------

**Vertices** and **polygons** for object, that we cut, **matrix** for this object to deform, translate before cut. **Cut matrix** - it is plane, that defined by matrix (translation+rotation).

Parameters
----------

table

+------------------+---------------+-----------------------------------------------------------------+
| Param            | Type          | Description                                                     |
+==================+===============+=================================================================+
| **Fill section** | Bool          | Make polygons or edges                                          |
+------------------+---------------+-----------------------------------------------------------------+
| **Alt+F/F**      | Bool          | If polygons, than triangles or single polygon                   |
+------------------+---------------+-----------------------------------------------------------------+

.. image:: https://user-images.githubusercontent.com/14288520/198751510-df7f9d23-5ca4-476c-8953-9081b5b88c7b.png
  :target: https://user-images.githubusercontent.com/14288520/198751510-df7f9d23-5ca4-476c-8953-9081b5b88c7b.png

Outputs
-------

**Vertices** and **Edges/Polygons**.

Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4222739/260e6252-3916-11e4-8044-66b70f3e15c9.jpg
  :target: https://cloud.githubusercontent.com/assets/5783432/4222739/260e6252-3916-11e4-8044-66b70f3e15c9.jpg
  :alt: cross_section.jpg

* Generator-> :doc:`Sphere </nodes/generator/sphere>`
* Float Serier (Old node): Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://user-images.githubusercontent.com/14288520/198751767-869bcfae-1ada-4fc7-bd54-e90d80bb9113.png
  :target: https://user-images.githubusercontent.com/14288520/198751767-869bcfae-1ada-4fc7-bd54-e90d80bb9113.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Analyzers-> :doc:`Bounding Box </nodes/analyzer/bbox_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`