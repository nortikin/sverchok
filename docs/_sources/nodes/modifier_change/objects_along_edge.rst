Duplicate Objects Along Edge
============================

.. image:: https://user-images.githubusercontent.com/14288520/201220460-0bd7d0b2-dcf7-4c93-91b5-a928d266b9ef.png
  :target: https://user-images.githubusercontent.com/14288520/201220460-0bd7d0b2-dcf7-4c93-91b5-a928d266b9ef.png

Functionality
-------------

This node creates an array of copies of one (donor) mesh and aligns it along
given recipient segment (edge). Count of objects in array can be specified by
user or detected automatically, based on size of donor mesh and length of
recipient edge. Donor mesh can be scaled automatically to fill all length of
recipient edge.

Donor objects are rotated so that specified axis of object is aligned to recipient edge.

It is in general not a trivial task to rotate a 3D object along a vector,
because there are always 2 other axes of object and it is not clear where
should they be directed to. So, this node supports 3 different algorithms of
object rotation calculation. In many simple cases, all these algorithms will
give exactly the same result. But in more complex setups, or in some corner
cases, results can be very different. So, just try all algorithms and see which
one fits you better.

This node also can output transformation matrices, which should be applied to
donor object to be aligned along recipient edge. By default, this node already
applies that matrices to donor object; but you can turn this off, and apply
matrices to donor object in another node, or apply them to different objects.

.. image:: https://user-images.githubusercontent.com/14288520/201313387-af1ecff3-b4c1-46df-8e14-2f2a5128df58.png
  :target: https://user-images.githubusercontent.com/14288520/201313387-af1ecff3-b4c1-46df-8e14-2f2a5128df58.png

Inputs
------

This node has the following inputs:

- **Vertices**. Vertices of the donor mesh. The node will produce nothing if
  this input is not connected.
- **Edges**. Edges of the donor mesh.
- **Polygons**. Faces of the donor mesh.

.. image:: https://user-images.githubusercontent.com/14288520/201330888-49b42b2e-fd4f-49a3-91d5-6c08863a9bd6.png
  :target: https://user-images.githubusercontent.com/14288520/201330888-49b42b2e-fd4f-49a3-91d5-6c08863a9bd6.png

- **Vertex1**. First vertex of recipient edge. This input is used only when
  "Fixed" input mode is used (see description of ``Input mode`` parameter
  below).
- **Vertex2**. Second vertex of recipient edge. This input is used only when
  "Fixed" input mode is used.

.. image:: https://user-images.githubusercontent.com/14288520/201330149-7ccb866a-38be-4f61-87d9-18df92ccac3d.png
  :target: https://user-images.githubusercontent.com/14288520/201330149-7ccb866a-38be-4f61-87d9-18df92ccac3d.png

- **VerticesR**. Vertices of the recipient mesh. This input is used only when
  "Edges" input mode is used.
- **EdgesR**. Edges of the recipient mesh. These edges will be actually used as
  recipient edges.  This input is used only when "Edges" input mode is used.

.. image:: https://user-images.githubusercontent.com/14288520/201318700-6bed15f8-471a-41a1-820f-92c37bcd9630.png
  :target: https://user-images.githubusercontent.com/14288520/201318700-6bed15f8-471a-41a1-820f-92c37bcd9630.png

- **Count**. Number of objects in array. This input is used only in "Count"
  scaling mode (see description of ``Scale mode`` parameter below). Number-> :doc:`List Input </nodes/number/list_input>` allowed to connect to count socket.

.. image:: https://user-images.githubusercontent.com/14288520/201315561-08dcae28-9277-44c0-8763-ed3260406482.png
  :target: https://user-images.githubusercontent.com/14288520/201315561-08dcae28-9277-44c0-8763-ed3260406482.png

.. image:: https://user-images.githubusercontent.com/14288520/201333288-53c3d8db-5822-47e7-875f-8e71e4c364f6.png
  :target: https://user-images.githubusercontent.com/14288520/201333288-53c3d8db-5822-47e7-875f-8e71e4c364f6.png

- **Padding**. Portion of the recipient edge length that should be left empty
  from both sides. Default value of zero means fill whole available length.

.. image:: https://user-images.githubusercontent.com/14288520/201314412-8f420136-b4a3-4ca6-9431-7b441d3f0cfc.png
  :target: https://user-images.githubusercontent.com/14288520/201314412-8f420136-b4a3-4ca6-9431-7b441d3f0cfc.png

Parameters
----------

This node has the following parameters:

+------------------+----------------+-------------+--------------------------------------------------------------------+
| Parameter        | Type           | Default     | Description                                                        |
+==================+================+=============+====================================================================+
| **Scaling**      | Count          | Count       | **Count**: specify number of objects in array. Objects scale       |
|                  |                |             |                                                                    |
| **mode**         | Up             |             | will be calculated so that copies will fill length of              |
|                  |                |             |                                                                    |
|                  |                |             | recipient edge.                                                    |
|                  |                |             |                                                                    |
|                  | Down           |             | **Up**: count is determined automatically from length of           |
|                  |                |             |                                                                    |
|                  |                |             | recipient edge and size of donor mesh, and meshes are              |
|                  |                |             |                                                                    |
|                  |                |             | scaled only up (for example, if donor mesh is 1 unit long,         |
|                  |                |             |                                                                    |
|                  |                |             | and recipient edge is 3.6 units, then there will be 3              |
|                  |                |             |                                                                    |
|                  |                |             | meshes scaled to be 1.2 units long each).                          |
|                  |                |             |                                                                    |
|                  | Off            |             | **Down**: the same as Up, but meshes are scaled only down.         |
|                  |                |             |                                                                    |
|                  |                |             | **Off**: the same as Up, but meshes are not scaled, so there       |
|                  |                |             |                                                                    |
|                  |                |             | will be some empty space between copies.                           |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Orientation**  | X / Y / Z      | X           | Which axis of donor object should be aligned to direction          |
|                  |                |             |                                                                    |
|                  |                |             | of the recipient edge.                                             |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Algorithm**    | Householder    | House       | **Householder**: calculate rotation by using Householder's         |
|                  |                |             |                                                                    |
|                  |                | holder      | reflection matrix (see Wikipedia_ article).                        |
|                  |                |             |                                                                    |
|                  | or Tracking    |             | **Tracking**: use the same algorithm as in Blender's "TrackTo"     |
|                  |                |             |                                                                    |
|                  |                |             | kinematic constraint. This algorithm gives you a bit more          |
|                  |                |             |                                                                    |
|                  |                |             | flexibility comparing to other, by allowing to select the Up       |
|                  |                |             |                                                                    |
|                  |                |             | axis.                                                              |
|                  |                |             |                                                                    |
|                  | or Rotation    |             | **Rotation difference**: calculate rotation as rotation            |
|                  |                |             |                                                                    |
|                  | Difference     |             | difference between two vertices.                                   |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Up axis**      | X / Y / Z      | Z           | Axis of donor object that should point up in result. This          |
|                  |                |             |                                                                    |
|                  |                |             | parameter is available only when Tracking algorithm is             |
|                  |                |             |                                                                    |
|                  |                |             | selected. Value of this parameter must differ from                 |
|                  |                |             |                                                                    |
|                  |                |             | **Orientation** parameter, otherwise you will get an error.        |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Input**        | Edges          | Edges       | **Edges**: recipient edges will be determined as all edges         |
|                  |                |             |                                                                    |
| **mode**         | or             |             | from the ``EdgesR`` input between vertices from                    |
|                  |                |             |                                                                    |
|                  | Fixed          |             | ``VerticesR`` input.                                               |
|                  |                |             |                                                                    |
|                  |                |             | **Fixed**: recipient edge will be determied as an edge             |
|                  |                |             |                                                                    |
|                  |                |             | between the edge from ``Vertex1`` input and the vertex             |
|                  |                |             |                                                                    |
|                  |                |             | from ``Vertex2`` input.                                            |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Scale all**    | Bool           | False       | If False, then donor object  will be scaled only along axis        |
|                  |                |             |                                                                    |
| **axes**         |                |             | is aligned with recipient edge direction. If True, objects         |
|                  |                |             |                                                                    |
|                  |                |             | will be scaled along all axes (by the same factor).                |
|                  |                |             |                                                                    |
|                  |                |             | This parameter is available only in the N panel.                   |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Apply**        | Bool           | True        | Whether to apply calculated matrices to created objects.           |
|                  |                |             |                                                                    |
| **matrices**     |                |             | This parameter is available only in the N panel.                   |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Count**        | Int            | 3           | Number of objects in array. This parameter can be                  |
|                  |                |             |                                                                    |
|                  |                |             | determined from the corresponding input. It is used only           |
|                  |                |             |                                                                    |
|                  |                |             | in "Count" scaling mode.                                           |
+------------------+----------------+-------------+--------------------------------------------------------------------+
| **Padding**      | Float          | 0.0         | Portion of the recipient edge length that should be                |
|                  |                |             |                                                                    |
|                  |                |             | left empty from both sides. Default value of zero means            |
|                  |                |             |                                                                    |
|                  |                |             | fill whole length available. Maximum value 0.49 means              |
|                  |                |             |                                                                    |
|                  |                |             | use only central 1% of edge.                                       |
+------------------+----------------+-------------+--------------------------------------------------------------------+

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**
- **Polygons**
- **Matrices**. Matrices that should be applied to created objects to align
  them along recipient edge. By default, this node already applies these
  matrices, so you do not need to do it second time.

.. image:: https://user-images.githubusercontent.com/14288520/201331535-cab0d823-8dac-42bf-bbe3-de480356612a.png
  :target: https://user-images.githubusercontent.com/14288520/201331535-cab0d823-8dac-42bf-bbe3-de480356612a.png

This node will output something only when ``Vertices`` or ``Matrices`` output is connected.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/14288520/201381243-2d7a2132-2473-49cf-abfa-b4a7070b861d.png
  :target: https://user-images.githubusercontent.com/14288520/201381243-2d7a2132-2473-49cf-abfa-b4a7070b861d.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator->Generators Extended :doc:`Torus Knot </nodes/generators_extended/torus_knot_mk2>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color Ramp </nodes/color/color_ramp>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

Suzanne duplicated along the segment between two specified points:

.. image:: https://user-images.githubusercontent.com/14288520/201382773-7fdb06b4-8361-442f-bbda-d61ad9da9dff.png
  :target: https://user-images.githubusercontent.com/14288520/201382773-7fdb06b4-8361-442f-bbda-d61ad9da9dff.png

* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Generator-> :doc:`Segment </nodes/generator/segment>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Suzannes duplicated along the edges of Box:

.. image:: https://user-images.githubusercontent.com/14288520/201384581-6f1bcd4a-ff14-4aaa-bf02-459b090e2d6c.png
  :target: https://user-images.githubusercontent.com/14288520/201384581-6f1bcd4a-ff14-4aaa-bf02-459b090e2d6c.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Suzanne </nodes/generator/suzanne>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Complex object duplicated along circle:

.. image:: https://user-images.githubusercontent.com/14288520/201387261-bad089f0-ea89-4d96-b895-00555ed3458c.png
  :target: https://user-images.githubusercontent.com/14288520/201387261-bad089f0-ea89-4d96-b895-00555ed3458c.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator->Generators Extended :doc:`Torus Knot </nodes/generators_extended/torus_knot_mk2>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* List-> :doc:`Index To Mask </nodes/list_masks/index_to_mask>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


You can also find more examples and some discussion `in the development thread <https://github.com/portnov/sverchok/issues/6>`_.

