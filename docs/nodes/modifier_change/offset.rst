Offset
======

*destination after Beta: Modifier Change*

.. image:: https://user-images.githubusercontent.com/14288520/198389030-a350590c-5bc6-4d62-97f4-168089f275d7.png
  :target: https://user-images.githubusercontent.com/14288520/198389030-a350590c-5bc6-4d62-97f4-168089f275d7.png

Functionality
-------------

Make offset for polygons with bevel in corners. Output inner and outer polygons separately.

.. image:: https://user-images.githubusercontent.com/14288520/198391035-85e9ac62-fe9f-4c32-8ac6-9061824d1dd2.png
  :target: https://user-images.githubusercontent.com/14288520/198391035-85e9ac62-fe9f-4c32-8ac6-9061824d1dd2.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`

Inputs
------

This node has the following inputs:

- **Vers** - vertices of objects
- **Pols** - polygons of objects
- **offset** - offset values. Vectorized for every polygon as [[f,f,f,f,f]]
- **nsides** - number of rounded sides
- **radius** - bevel radius. Vectorized for every polygon as [[f,f,f,f,f]]

.. image:: https://user-images.githubusercontent.com/14288520/198395930-ec31a765-51b3-4cc9-9198-cd96099d930c.png
  :target: https://user-images.githubusercontent.com/14288520/198395930-ec31a765-51b3-4cc9-9198-cd96099d930c.png

* Number-> :doc:`Number Range </nodes/number/number_range>`

Parameters
----------

All parameters can be given by the node or an external input.
``offset`` and ``radius`` are vectorized and they will accept single or multiple values.

+-----------------+---------------+-------------+-------------------------------------------------------------+
| Param           | Type          | Default     | Description                                                 |
+=================+===============+=============+=============================================================+
| **offset**      | Float         | 0.04        | offset values.                                              |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **nsides**      | Integer       | 1           | number of rounded sides.                                    |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **radius**      | Float         | 0.04        | bevel radius.                                               |
+-----------------+---------------+-------------+-------------------------------------------------------------+


Outputs
-------

This node has the following outputs:

- **Vers**
- **Edgs**
- **OutPols** - get polygons that lay in outer polygon's line.
- **InPols** - get polygons that lay in inner polygon's line.

.. image:: https://user-images.githubusercontent.com/14288520/198396663-60cd7f42-e708-4042-aa9b-183409fa2676.png
  :target: https://user-images.githubusercontent.com/14288520/198396663-60cd7f42-e708-4042-aa9b-183409fa2676.png

See also
--------

* CAD-> :doc:`Inscribed Circle </nodes/analyzer/inscribed_circle>`
* CAD-> :doc:`Steiner Ellipse </nodes/analyzer/steiner_ellipse>`

Examples of usage
-----------------

Offset and radius are defined by distance between point and polygon's center, divided by some number:

.. image:: https://user-images.githubusercontent.com/14288520/198399486-6c35dc6b-8cd4-4673-8594-84e00a9dfb3d.png
  :target: https://user-images.githubusercontent.com/14288520/198399486-6c35dc6b-8cd4-4673-8594-84e00a9dfb3d.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://user-images.githubusercontent.com/14288520/198399530-ed4fa6db-c6c2-4aac-91fc-5ef6f723803a.gif
  :target: https://user-images.githubusercontent.com/14288520/198399530-ed4fa6db-c6c2-4aac-91fc-5ef6f723803a.gif

---------

Parameters' cases, that make different polygons (decomposer list node used to separate):

.. image:: https://user-images.githubusercontent.com/14288520/198401754-ec11ec2a-2d9d-4298-84c6-4a1f368fddca.png
  :target: https://user-images.githubusercontent.com/14288520/198401754-ec11ec2a-2d9d-4298-84c6-4a1f368fddca.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* List->List Main-> :doc:`List Decompose </nodes/list_main/decompose>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`

---------

Upper image can be defined by one offset and list (range) of numbers, plugged to offset/radius, which are vectorised:

.. image:: https://user-images.githubusercontent.com/14288520/198402357-4ed1ba2d-d21a-487f-acd8-fc0a5045602b.png
  :target: https://user-images.githubusercontent.com/14288520/198402357-4ed1ba2d-d21a-487f-acd8-fc0a5045602b.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`