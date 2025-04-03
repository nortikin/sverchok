Area
=====

.. image:: https://user-images.githubusercontent.com/14288520/195365832-e25b9df7-6038-4a04-9489-ff75dea36c7a.png
  :target: https://user-images.githubusercontent.com/14288520/195365832-e25b9df7-6038-4a04-9489-ff75dea36c7a.png

Functionality
-------------

Area node is one of the analyzer type. It is used to get the area of any polygon, no matter the number of its vertices or its world position.

Inputs
------

**Vertices** and **Polygons** are needed. 
Both inputs need to be of the kind Vertices and Strings, respectively

Parameters
----------

All parameters need to proceed from an external node.


+------------------+---------------+-------------+-----------------------------------------------+
| Param            | Type          | Default     | Description                                   |
+==================+===============+=============+===============================================+
| **Vertices**     | Vertices      | None        | vertices of the polygons                      |
+------------------+---------------+-------------+-----------------------------------------------+
| **Polygons**     | Strings       | None        | polygons referenced to vertices               |
+------------------+---------------+-------------+-----------------------------------------------+
| **Count Faces**  | Boolean       | True        | output individual faces or the sum of all     |
+------------------+---------------+-------------+-----------------------------------------------+

Outputs
-------

**Area** will be calculated only if both **Vertices** and **Polygons** inputs are linked.

See also
--------

* Analyzers-> :ref:`Component Analyzer/Faces/Area <FACES_AREA>`


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/195367229-67a81667-6b71-46f6-abce-cbc4bfc8e74f.png
  :target: https://user-images.githubusercontent.com/14288520/195367229-67a81667-6b71-46f6-abce-cbc4bfc8e74f.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Text-> :doc:`String Tools </nodes/text/string_tools>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Viz-> :doc:`Viewer Index+ </nodes/viz/viewer_idx28>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

In the example we have the inputs from a plane with 16 faces. You can use **Area** node to get the sum of all of them or the area of every face individually.