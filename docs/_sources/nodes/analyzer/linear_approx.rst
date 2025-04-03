Linear Approximation
====================

.. image:: https://user-images.githubusercontent.com/14288520/197297060-40905343-6035-4de0-bcc6-71d135b22342.png
  :target: https://user-images.githubusercontent.com/14288520/197297060-40905343-6035-4de0-bcc6-71d135b22342.png

Functionality
-------------

This node tries to approximate provided set of vertices by either a plane or
a straight line. In other words, it searches for such a plane / line, that all
provided vertices have the minimum distance to it.

More technically, it searches for a plane or a line A, such that

.. image:: https://user-images.githubusercontent.com/284644/58372582-e6e25700-7f38-11e9-844f-aaa4fa2bb562.gif

The plane is represented by a point on the plane and a normal vector.

The line is represented by a point on the line and a direction vector.

That point on line or plane is calculated as a geometrical center of all
provided vertices.

Inputs
------

This node has one input: **Vertices** - the vertices to be approximated.

Parameters
----------

This node has one parameter - **Mode**. Two modes are supported:

* **Line** - approximate vertices by straight line. This is the default mode.
* **Plane** - approximate vertices by a plane.

Outputs
-------

This node has the following outputs:

* **Center** - the point on the line or plane. This is geometrical center of all input vertices.
* **Normal** - the normal vector of a plane. This output is only available in the **Plane** mode.
* **Direction** - the direction vector of a line. This output is only available in the **Line** mode.
* **Projections** - the projections of input vertices to the line or plane.
* **Diffs** - difference vectors between the input vertices and their projections to line or plane.
* **Distances** - distances between the input vertices and their projections to line or plane.

.. image:: https://user-images.githubusercontent.com/14288520/197299824-7ae8ee67-9b0a-4ee0-936b-108e8938d28a.png
  :target: https://user-images.githubusercontent.com/14288520/197299824-7ae8ee67-9b0a-4ee0-936b-108e8938d28a.png

.. image:: https://user-images.githubusercontent.com/14288520/197300411-ae974cb0-087e-4a8e-ba79-0a4941e29143.gif
  :target: https://user-images.githubusercontent.com/14288520/197300411-ae974cb0-087e-4a8e-ba79-0a4941e29143.gif

---------

.. image:: https://user-images.githubusercontent.com/14288520/197305783-fef73a2c-50a4-49dd-b3b5-d3b1e398982b.png
  :target: https://user-images.githubusercontent.com/14288520/197305783-fef73a2c-50a4-49dd-b3b5-d3b1e398982b.png

.. image:: https://user-images.githubusercontent.com/14288520/197305728-f681a3e0-7dee-4e60-8a26-a5b1d6a2e08f.gif
  :target: https://user-images.githubusercontent.com/14288520/197305728-f681a3e0-7dee-4e60-8a26-a5b1d6a2e08f.gif

Examples of usage
-----------------

The simplest example: approximate 3D curve by a line. Here black curve is a
grease pencil, green one - it's representation in Sverchok, red line - result
of linear approximation of green line.

.. image:: https://user-images.githubusercontent.com/284644/58330560-8e378f00-7e50-11e9-9bf5-8612c420ed91.png
    :target: https://user-images.githubusercontent.com/284644/58330560-8e378f00-7e50-11e9-9bf5-8612c420ed91.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector Interpolation </nodes/vector/interpolation_mk3>`
* Modifiers->Modifier Make-> :doc:`UV Connection </nodes/modifier_make/uv_connect>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

A simple example with plane.

.. image:: https://user-images.githubusercontent.com/284644/58274029-63472f80-7dab-11e9-9c8b-1953633cf2be.png
    :target: https://user-images.githubusercontent.com/284644/58274029-63472f80-7dab-11e9-9c8b-1953633cf2be.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Matrix-> :doc:`Matrix Track To </nodes/matrix/matrix_track_to>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The node can calculate approximation for several sets of vertices at once:

.. image:: https://user-images.githubusercontent.com/284644/58273750-cd130980-7daa-11e9-8f99-3ec57b37965c.png
    :target: https://user-images.githubusercontent.com/284644/58273750-cd130980-7daa-11e9-8f99-3ec57b37965c.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Matrix-> :doc:`Matrix Track To </nodes/matrix/matrix_track_to>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


You can also find more examples and some discussion `in the development thread <https://github.com/nortikin/sverchok/pull/2421>`_.

