Bricks Grid
===========

.. image:: https://user-images.githubusercontent.com/14288520/190888043-47886557-91b2-498f-a939-eb4ea881af87.png
  :target: https://user-images.githubusercontent.com/14288520/190888043-47886557-91b2-498f-a939-eb4ea881af87.png

Functionality
-------------

This node generates bricks-like grid, i.e. a grid each row of which is shifted
with relation to another. It is also possible to specify toothing, so it will
be like engaged bricks.
All parameters of bricks can be randomized with separate control over
randomization of each parameter.

Optionally the grid may be cyclic in one or two directions. This can be useful
if you are going to map the grid onto some sort of cyclic or toroidal surface.

.. image:: https://user-images.githubusercontent.com/14288520/190888015-c19cc1ea-f742-4216-9bc6-bdb8ed9a77b5.png
  :target: https://user-images.githubusercontent.com/14288520/190888015-c19cc1ea-f742-4216-9bc6-bdb8ed9a77b5.png


Inputs & Parameters
-------------------

All parameters except for ``Faces mode`` can be given by the node or an external input.
All inputs are vectorized and they will accept single or multiple values.

+-----------------+---------------+-------------+-------------------------------------------------------------+
| Param           | Type          | Default     | Description                                                 |
+=================+===============+=============+=============================================================+
| **Cycle U**     | Boolean       | False       | Make the grid cyclic in U direction, i.e. the direction of  |
|                 |               |             |                                                             |
|                 |               |             | brick rows. This makes sense only if you are going to map   |
|                 |               |             |                                                             |
|                 |               |             | the grid on to some sort of cyclic surface (e.g. cylinder). |
|                 |               |             |                                                             |
|                 |               |             | **Note**: after such mapping, you may want to use "Remove   |
|                 |               |             |                                                             |
|                 |               |             | doubles" node.                                              |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Cycle V**     | Boolean       | False       | Make the grid cyclic in V direction, i.e. the direction of  |
|                 |               |             |                                                             |
|                 |               |             | brick columns. This makes sense only if you are going       |
|                 |               |             |                                                             |
|                 |               |             | to map the grid on to some sort of cyclic surface (e.g..    |
|                 |               |             |                                                             |
|                 |               |             | cylinder)                                                   |
|                 |               |             |                                                             |
|                 |               |             | **Note**: after such mapping, you may want to use "Remove   |
|                 |               |             |                                                             |
|                 |               |             | doubles" node.                                              |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Faces mode**  | Flat or       | Flat        | What kind of polygons to generate:                          |
|                 |               |             |                                                             |
|                 | Stitch or     |             | **Flat** - generate one polygon (n-gon, in general)         |
|                 |               |             |                                                             |
|                 |               |             | for each brick.                                             |
|                 |               |             |                                                             |
|                 | Center        |             | **Stitch** - split each brick into several triangles,       |
|                 |               |             |                                                             |
|                 |               |             | with edges going across brick.                              |
|                 |               |             |                                                             |
|                 |               |             | **Center** - split each brick into triangles by             |
|                 |               |             |                                                             |
|                 |               |             | adding new vertex in the center of the brick.               |
|                 |               |             |                                                             |
|                 |               |             | This mode is not available if *any* of                      |
|                 |               |             |                                                             |
|                 |               |             | **Cycle U**, **Cycle V** parameters is checked.             |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Unit width**  | Float         | 2.0         | Width of one unit (brick).                                  |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Unit height** | Float         | 1.0         | Height of one unit (brick).                                 |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Width**       | Float         | 10.0        | Width of overall grid.                                      |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Height**      | Float         | 10.0        | Height of overall grid.                                     |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Toothing**    | Float         | 0.0         | Bricks toothing amount. Default value of zero means no      |
|                 |               |             |                                                             |
|                 |               |             | toothing.                                                   |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Toothing      | Float         | 0.0         | Toothing randomization factor. Default value of zero        |
| random**        |               |             |                                                             |
|                 |               |             | means that all toothings will be equal. Maximal value       |
|                 |               |             |                                                             |
|                 |               |             | of 1.0 means toothing will be random in range from zero     |
|                 |               |             |                                                             |
|                 |               |             | to value of ``Toothing`` parameter.                         |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Random U**    | Float         | 0.0         | Randomization amplitude along bricks rows. Default          |
|                 |               |             |                                                             |
|                 |               |             | value of zero means all bricks will be of same width.       |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Random V**    | Float         | 0.0         | Randomization amplitude across bricks rows. Default         |
|                 |               |             |                                                             |
|                 |               |             | value of zero means all grid rows will be of same height.   |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Shift**       | Float         | 0.5         | Brick rows shift factor. Default value of 0.5 means each    |
|                 |               |             |                                                             |
|                 |               |             | row of bricks will be shifted by half of brick width in     |
|                 |               |             |                                                             |
|                 |               |             | relation to previous row. Minimum value of zero means       |
|                 |               |             |                                                             |
|                 |               |             | no shift.                                                   |
+-----------------+---------------+-------------+-------------------------------------------------------------+
| **Seed**        | Int           | 0           | Random seed.                                                |
+-----------------+---------------+-------------+-------------------------------------------------------------+

Outputs
-------

This node has the following outputs:

- **Vertices**
- **Edges**. Note that this output will contain only edges that are between bricks, not that splitting bricks into triangles.
- **Polygons**
- **Centers**. Centers of bricks.

Examples of usage
-----------------

Default settings:

.. image:: https://user-images.githubusercontent.com/14288520/190888700-530a8d23-b263-44a8-aaa1-4f79dd0a3c8f.png
  :target: https://user-images.githubusercontent.com/14288520/190888700-530a8d23-b263-44a8-aaa1-4f79dd0a3c8f.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The same with Stitch faces mode:

.. image:: https://user-images.githubusercontent.com/14288520/190897076-5e66d880-a1d8-4f92-8812-a47c99296904.png
  :target: https://user-images.githubusercontent.com/14288520/190897076-5e66d880-a1d8-4f92-8812-a47c99296904.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The same with Centers faces mode:

.. image:: https://user-images.githubusercontent.com/14288520/190897098-7f951422-4e61-4c25-affc-95d598b3645e.png
  :target: https://user-images.githubusercontent.com/14288520/190897098-7f951422-4e61-4c25-affc-95d598b3645e.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Using ``toothing`` parameter together with randomization, it is possible to generate something like stone wall:

.. image:: https://user-images.githubusercontent.com/14288520/190888712-6be35135-3f51-4ce0-bfed-dbac6fc33caf.png
  :target: https://user-images.githubusercontent.com/14288520/190888712-6be35135-3f51-4ce0-bfed-dbac6fc33caf.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

A honeycomb structure:

.. image:: https://user-images.githubusercontent.com/14288520/190888980-59d2e3f3-e079-4f6e-aed1-4ab110e7b48b.png
  :target: https://user-images.githubusercontent.com/14288520/190888980-59d2e3f3-e079-4f6e-aed1-4ab110e7b48b.png

* Modifier Change-> :doc:`Offset </nodes/modifier_change/offset>`
* Modifier Make-> :doc:`Solidify </nodes/modifier_make/solidify_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Wooden floor:

.. image:: https://user-images.githubusercontent.com/14288520/190889070-2dcd345c-9c60-4568-a0a0-ec5e36a49b26.png
  :target: https://user-images.githubusercontent.com/14288520/190889070-2dcd345c-9c60-4568-a0a0-ec5e36a49b26.png

* Modifier Change-> :doc:`Offset </nodes/modifier_change/offset>`
* Modifier Make-> :doc:`Solidify </nodes/modifier_make/solidify_mk2>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

You can also find some more examples `in the development thread <https://github.com/portnov/sverchok/issues/19>`_.

