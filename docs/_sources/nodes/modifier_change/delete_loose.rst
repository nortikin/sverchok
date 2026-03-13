Delete Loose
============

.. image:: https://user-images.githubusercontent.com/14288520/199105666-aae33182-7981-4ac2-863a-09370164125b.png
  :target: https://user-images.githubusercontent.com/14288520/199105666-aae33182-7981-4ac2-863a-09370164125b.png

Functionality
-------------

Delete Loose vertices, that not belong to edges or polygons that plugged in.

.. image:: https://user-images.githubusercontent.com/14288520/199107411-024aa667-fd50-4335-abf7-f04ba5558462.png
  :target: https://user-images.githubusercontent.com/14288520/199107411-024aa667-fd50-4335-abf7-f04ba5558462.png

Inputs
------

- **Vertices**
- **PolyEdge**

Outputs
-------

- **Vertices** - filtered
- **PolyEdge**

Examples of usage
-----------------

Simple:

.. image:: https://user-images.githubusercontent.com/14288520/199108536-900db4f5-4347-48fe-8ccc-5dbb748c188b.png
  :target: https://user-images.githubusercontent.com/14288520/199108536-900db4f5-4347-48fe-8ccc-5dbb748c188b.png

* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`