Offset Line
===========

.. image:: https://user-images.githubusercontent.com/14288520/200897605-00613b3c-10ba-4e23-8d32-cfa51dec461d.png
  :target: https://user-images.githubusercontent.com/14288520/200897605-00613b3c-10ba-4e23-8d32-cfa51dec461d.png

Functionality
-------------

This node works only in XY surface. It takes X and Y coordinate from vectors input. Also Z coordinate is used now but this node is still work like 2D node. Z coordinate of the new points is equal z coordinate of the nearest old points. So if you use z coordinate you have to remember:

- All points are projected to the XY surface so you can use Z coordinate for showing different levels of a flat mesh.
- Vertical edges will broke down work of the node.
- Normals of all faces always look to up.

Use ``delete loose`` node before if your input mesh has points without edges. You will receive surface along an input mesh edges with width equal offset value. It is also available to receive outer edges and mask of new and old points.

.. image:: https://user-images.githubusercontent.com/14288520/200904381-29e18316-91d6-4cb0-ad7a-a3e3190f1bf6.png
  :target: https://user-images.githubusercontent.com/14288520/200904381-29e18316-91d6-4cb0-ad7a-a3e3190f1bf6.png

Inputs
------

This node has the following inputs:

- **Vers** - vertices of objects.
- **Edgs** - polygons of objects.
- **offset** - offset values - available multiple value per object (greater than 0. 0 will replace by 0.001).

Parameters
----------

All parameters can be given by the node or an external input.
``offset`` is vectorized and it will accept single or multiple values.

+-----------------+---------------+-------------+-------------------------------------------------------------+
| Param           | Type          | Default     | Description                                                 |
+=================+===============+=============+=============================================================+
| **offset**      | Float         | 0.10        | offset values.                                              |
+-----------------+---------------+-------------+-------------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vers**
- **Faces**
- **OuterEdges** - get outer edges, use together with ``delete loose`` node after or ``mask verts``. The list of edges is unordered.
- **VersMask** - 0 for new points and 1 for old.

.. image:: https://user-images.githubusercontent.com/14288520/200906483-088c0f6c-c5de-4718-8f25-31dbba173e97.png
  :target: https://user-images.githubusercontent.com/14288520/200906483-088c0f6c-c5de-4718-8f25-31dbba173e97.png

Examples of usage
-----------------

To receive offset from input object from scene:

.. image:: https://user-images.githubusercontent.com/28003269/34199193-5e1281a4-e586-11e7-97b8-f1984facdfcb.png
  :target: https://user-images.githubusercontent.com/28003269/34199193-5e1281a4-e586-11e7-97b8-f1984facdfcb.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using of outer edges:

.. image:: https://user-images.githubusercontent.com/28003269/34199326-dadbf508-e586-11e7-9542-7b7ff4a9521f.png
  :target: https://user-images.githubusercontent.com/28003269/34199326-dadbf508-e586-11e7-9542-7b7ff4a9521f.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Modifiers->Modifier Change-> :doc:`Delete Loose </nodes/modifier_change/delete_loose>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using of vertices mask with ``transform select`` node:

.. image:: https://user-images.githubusercontent.com/28003269/34199698-125ed63e-e588-11e7-9e34-83c5eb33cde9.png
  :target: https://user-images.githubusercontent.com/28003269/34199698-125ed63e-e588-11e7-9e34-83c5eb33cde9.png

* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Transform-> :doc:`Transform Select </nodes/transforms/transform_select>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Different values for each object and each point:

.. image:: https://user-images.githubusercontent.com/28003269/34353407-47f2d918-ea41-11e7-92c0-f0f9751e4cab.png
  :target: https://user-images.githubusercontent.com/28003269/34353407-47f2d918-ea41-11e7-92c0-f0f9751e4cab.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using of Z coordinate:

.. image:: https://user-images.githubusercontent.com/14288520/200909050-34199e42-54aa-41cf-9efb-abef230afdf7.png
  :target: https://user-images.githubusercontent.com/14288520/200909050-34199e42-54aa-41cf-9efb-abef230afdf7.png

* Scene-> :doc:`Get Objects Data </nodes/scene/get_objects_data>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`