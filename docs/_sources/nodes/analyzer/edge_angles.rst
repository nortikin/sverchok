Angles at the Edges
===================

.. image:: https://user-images.githubusercontent.com/14288520/196689431-6904db77-898c-4d02-8dfb-04ff75533048.png
  :target: https://user-images.githubusercontent.com/14288520/196689431-6904db77-898c-4d02-8dfb-04ff75533048.png

*This node testing is in progress, so it can be found under Beta menu*

Functionality
-------------

This node calculates angles at the edges of input mesh. Angles can be measured in radians or degrees.

Inputs
------

This node has the following inputs:

- **Vertices**.
- **Edges**. Note that this input should be connected in order for output angles to be in correct order.
- **Polygons**.

Parameters
----------

This node has the following parameters:

+------------------+----------------+-------------+------------------------------------------------------------------+
| Parameter        | Type           | Default     | Description                                                      |
+==================+================+=============+==================================================================+
| **Signed**       | Boolean        | False       | If checked, then the node will output negative values            |
|                  |                |             |                                                                  |
|                  |                |             | for concave edges. By default, it always outputs                 |
|                  |                |             |                                                                  |
|                  |                |             | positive angles.                                                 |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Complement**   | Boolean        | False       | Output complementary angle to one calculated by BMesh.           |
|                  |                |             |                                                                  |
|                  |                |             | BMesh assumes that angle between two complanar faces             |
|                  |                |             |                                                                  |
|                  |                |             | is zero. With this flag checked, the node will output            |
|                  |                |             |                                                                  |
|                  |                |             | PI (or 180) for angle between complanar faces.                   |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Wire/**        | Enum           | Default     | What to return as angle for wire or boundary edges.              |
|                  |                |             |                                                                  |
| **Boundary**     |                |             | BMesh returns some angle by default for such                     |
|                  |                |             |                                                                  |
| **value**        |                |             | edges, but in some cases these values do not make                |
|                  |                |             |                                                                  |
|                  |                |             | sense.                                                           |
|                  |                |             |                                                                  |
|                  |                |             | This parameter is displayed only in N panel.                     |
|                  |                |             |                                                                  |
|                  |                |             | Default.                                                         |
|                  |                |             |    Use value returned by BMesh.                                  |
|                  |                |             | Zero.                                                            |
|                  |                |             |    Return zero.                                                  |
|                  |                |             | Pi.                                                              |
|                  |                |             |    Return PI (or 180).                                           |
|                  |                |             | Pi/2.                                                            |
|                  |                |             |    Return PI/2 (or 90).                                          |
|                  |                |             | None.                                                            |
|                  |                |             |    Return None.                                                  |
+------------------+----------------+-------------+------------------------------------------------------------------+
| **Angles mode**  | Enum           | Radian      | Whether to measure angles in radians or in degrees.              |
+------------------+----------------+-------------+------------------------------------------------------------------+

Outputs
-------

This node has one output: **Angles**. The output contains calculated angles at the edges of input mesh. Angles are in the order of edges in the ``Edges`` input. If the ``Edges`` input is not connected or is empty, then angles will be in order returned by BMesh, which is, strictly speaking, random order.

Example of usage
----------------

Bevel only acute angles:

.. image:: https://user-images.githubusercontent.com/14288520/196697786-3233852c-99ff-4c52-b5c4-525a8953278d.png
  :target: https://user-images.githubusercontent.com/14288520/196697786-3233852c-99ff-4c52-b5c4-525a8953278d.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* CAD-> :doc:`Bevel </nodes/modifier_change/bevel>`
* LESS: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List-> :doc:`List Mask (Out) </nodes/list_masks/mask>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`