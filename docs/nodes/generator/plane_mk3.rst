Plane
=====

.. image:: https://user-images.githubusercontent.com/14288520/188589996-04c36fed-4aa5-4516-9eb6-a0d2b8367f52.png
  :target: https://user-images.githubusercontent.com/14288520/188589996-04c36fed-4aa5-4516-9eb6-a0d2b8367f52.png

.. image:: https://user-images.githubusercontent.com/14288520/188585376-c4853550-2093-4b10-b9f9-f94185508387.png
  :target: https://user-images.githubusercontent.com/14288520/188585376-c4853550-2093-4b10-b9f9-f94185508387.png

Functionality
-------------

Plane generator creates a grid in the plane XY/YZ or ZX, the node offers different methods to define the size of the grid and the spacing between the points.

**Size Mode**: the planar grid is defined by its total size and the number of vertices in both axis
**Number**: the planar grid is defined by the spacing of the vertices and the number of them
**Steps**: this mode expects a list with spacing between the vertices, it can support variable spacing
**Size + Steps**: similar to the Steps mode but normalizes the list to fit a defined size

Inputs and Parameters
---------------------

All parameters except **Direction**, **Center** can be given by the node or an external input.

+---------------+------------+-----------+----------------------------------------------------+
| Param         | Type       | Default   | Description                                        |
+===============+============+===========+====================================================+
| **Size X**    | Float      | 2         | number of vertices in X. The minimum is 2.         |
+---------------+------------+-----------+----------------------------------------------------+
| **Size Y**    | Float      | 2         | number of vertices in X. The minimum is 2.         |
+---------------+------------+-----------+----------------------------------------------------+
| **N Verts X** | Int        | 2         | number of vertices in X. The minimum is 2.         |
+---------------+------------+-----------+----------------------------------------------------+
| **N Verts Y** | Int        | 2         | number of vertices in X. The minimum is 2.         |
+---------------+------------+-----------+----------------------------------------------------+
| **Step X**    | Float      | 1.00      | length between vertices in X axis                  |
+---------------+------------+-----------+----------------------------------------------------+
| **Step Y**    | Float      | 1.00      | length between vertices in Y axis                  |
+---------------+------------+-----------+----------------------------------------------------+
| **Direction** | Enum       | XY        | generate grid in XY, YZ or ZX plane                |
+---------------+------------+-----------+----------------------------------------------------+
| **Center**    | Boolean    | False     | center the plane around origin                     |
+---------------+------------+-----------+----------------------------------------------------+
| **Matrix**    | Matrix     | None      | position, scale and rotation of the plane          |
+---------------+------------+-----------+----------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Simplify Output**: Method to keep output data suitable for most of the rest of the Sverchok nodes
  - None: Do not perform any change on the data. Only for advanced users
  - Join: The node will join the deepest level of planes in one object
  - Flat: It will flat the output to keep the one grid per object

**Match List Global**: Define how list with different lengths should be matched. Refers to the matching of groups (level 1)

**Match List Local**: Define how list with different lengths should be matched. Refers to the matching inside groups (level 2)

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). Available for Vertices, Edges and Polygons

Outputs
-------

**Vertices**, **Edges** and **Polygons**.
All outputs will be generated. Depending on the type of the inputs, the node will generate only one or multiples independent grids.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/188587154-3bd2509a-7060-42a5-a4dd-c3020b02ac5d.png
  :target: https://user-images.githubusercontent.com/14288520/188587154-3bd2509a-7060-42a5-a4dd-c3020b02ac5d.png

.. image:: https://user-images.githubusercontent.com/14288520/188587078-258847a6-f6df-4cab-84a5-6ca136388bd4.gif
  :target: https://user-images.githubusercontent.com/14288520/188587078-258847a6-f6df-4cab-84a5-6ca136388bd4.gif

* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Generating the same grid with different modes:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_0.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_0.png

* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`

Using the 'Steps' mode to control the grid spacing

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_01.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_01.png

* Number-> :doc:`Random Num Gen </nodes/number/random_num_gen>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

In the 'Si + St' mode (Size + Steps) the step list is used to control the proportion of the spacing between Vertices

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_02.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_02.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

With the list matching in 'cycle' advanced rhythms can be achieved.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_03.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_03.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* List->List Struct-> :doc:`List Split </nodes/list_struct/split>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

The matrix input is be vectorized and accepts many lists of matrixes, note in this example that the 'Flat Output' of the 'Matrix In' node is un-checked.

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_04.png
  :target: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/generators/plane/plane_node_sverchok_example_04.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

- The first 'Line' node generates one line with two verts.
- The second 'Line' node generates two lines with five verts.
- The 'Matrix In' node generates two list with five matrix in each list
- The Plane node will match the first matrix list with the first value of the 'List input' node (two vert per direction) and the second matrix list with the second value  of the 'List Input' node. 
