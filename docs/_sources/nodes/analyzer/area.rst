Area
=====

.. image:: https://github.com/user-attachments/assets/df35fcaf-c566-45d9-8b36-223e9cc9a9df
  :target: https://github.com/user-attachments/assets/df35fcaf-c566-45d9-8b36-223e9cc9a9df

Functionality
-------------

Area node is one of the analyzer type. It is used to get the area of any polygon or groups of polygons, no matter the number of its vertices or its world position.

Inputs
------

**Vertices** and **Polygons** are needed. 
Both inputs need to be of the kind Vertices and Strings, respectively

**Group by** - indexes per faces. Used to group faces by numbers.

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
| **Summ Faces**   | Boolean       | True        | output individual faces or the sum of all     |
+------------------+---------------+-------------+-----------------------------------------------+

Outputs
-------

**Area** will be calculated only if both **Vertices** and **Polygons** inputs are linked.
**Group by** - what group number for results areas if "Group by" used.

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

Get Areas of Suzanne's eyes
---------------------------

Here you can calculate the area of objects individually

  .. image:: https://github.com/user-attachments/assets/5426cae7-8e09-449d-a237-32f4eed24f23
    :target: https://github.com/user-attachments/assets/5426cae7-8e09-449d-a237-32f4eed24f23

Get Areas with mesh join
------------------------

Summarize areas by materials over all objects

  .. image:: https://github.com/user-attachments/assets/7bea18e5-29ab-4f24-8782-f8e343ce2ac2
    :target: https://github.com/user-attachments/assets/7bea18e5-29ab-4f24-8782-f8e343ce2ac2

The "Mesh Join" and "Post" properties allow you to objectify not only materials that are polygonal Mesh, but also Metaball, Beveled/Extruded Bezier, NURBS surfaces.

Get Areas of Beveled Bezier and Nurbs
-------------------------------------

  .. image:: https://github.com/user-attachments/assets/004b1204-40a5-4492-9e20-5fae3cfa7e65
    :target: https://github.com/user-attachments/assets/004b1204-40a5-4492-9e20-5fae3cfa7e65

You can use None material. In this case material will be None in the list.

Get Area of Bevel modifier
--------------------------

  .. image:: https://github.com/user-attachments/assets/e55fa8d0-8fda-477d-b457-751bf7846078
    :target: https://github.com/user-attachments/assets/e55fa8d0-8fda-477d-b457-751bf7846078

Get Area of Boolean modifier
----------------------------

  .. image:: https://github.com/user-attachments/assets/38c749e5-0164-42e3-aaef-fb0db74d0728
    :target: https://github.com/user-attachments/assets/38c749e5-0164-42e3-aaef-fb0db74d0728


Get Area of Solidify modifier
-----------------------------

  .. image:: https://github.com/user-attachments/assets/1b88f9bf-6299-454a-b849-6dd1f32c23aa
    :target: https://github.com/user-attachments/assets/1b88f9bf-6299-454a-b849-6dd1f32c23aa