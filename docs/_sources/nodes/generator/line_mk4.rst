Line
====

.. image:: https://user-images.githubusercontent.com/14288520/188509358-889793be-5e37-4024-9108-4530a5322218.png
  :target: https://user-images.githubusercontent.com/14288520/188509358-889793be-5e37-4024-9108-4530a5322218.png

.. image:: https://user-images.githubusercontent.com/14288520/188505902-9ae40896-37ba-4079-a654-c73ccfc71c37.png
  :target: https://user-images.githubusercontent.com/14288520/188505902-9ae40896-37ba-4079-a654-c73ccfc71c37.png

Functionality
-------------

The node can create line with origin in center of coordinate system and X, Y or Z direction
or with custom origin and direction. Also number of subdivisions can be set.

Category
--------

Generators -> Line

Inputs
------

- **Num Verts** - number of vertices of a line
- **Size** - length of a line
- **Step(s)** - distance between points of a line
- **Origin** - custom center of coordinate system
- **Direction** - direction of a line

Outputs
-------

- **Verts** - coordinates of line(s)
- **Edges** - just edges

Parameters
----------

.. image:: https://user-images.githubusercontent.com/14288520/188510773-fc5134d4-2969-48ef-8b84-a9e59b39dec5.png
  :target: https://user-images.githubusercontent.com/14288520/188510773-fc5134d4-2969-48ef-8b84-a9e59b39dec5.png

+---------------+---------------------+--------------+---------------------------------------------------------+
| Param         | Type                | Default      | Description                                             |
+===============+=====================+==============+=========================================================+
| **Direction** | Enum:               | "X"          | * X/Y/Z - Ortho direction                               | 
|               |                     |              |                                                         |
|               | X/Y/Z/OP/OD         |              | * OP - Origin and point on line                         |
|               |                     |              | * OD - Origin and Direction                             |
+---------------+---------------------+--------------+---------------------------------------------------------+
| **Length**    | Enum:               | "Size"       | Method of line size determination                       |
|               |                     |              |                                                         |
|               | Size/Num/Step/      |              |                                                         |
|               |                     |              |                                                         |
|               | St+Si               |              |                                                         |
+---------------+---------------------+--------------+---------------------------------------------------------+
| **Center**    | Boolean             | False        | center line in origin                                   |
+---------------+---------------------+--------------+---------------------------------------------------------+
| **Split to    | Boolean             |              |                                                         |
| objects**     | (N panel)           | True         | Each line will be put to separate object any way        |
+---------------+---------------------+--------------+---------------------------------------------------------+
| **Numpy       | Boolean             | False        | Convert vertices to Numpy array                         |
| output**      | (N panel)           |              |                                                         |
+---------------+---------------------+--------------+---------------------------------------------------------+

* **Step length mode** - expect array of steps with help of which a line can be subdivided into unequal parts.
* **Step + size mode** - expect array of steps with help of which a line can be subdivided into proportional parts with custom line length.

Example of usage
----------------

The first example shows just an standard line with 4 vertices and 1.00 ud between them

.. image:: https://user-images.githubusercontent.com/14288520/198871911-350fbb39-c61b-4236-9ea7-f3ce4aeaac2e.png
  :target: https://user-images.githubusercontent.com/14288520/198871911-350fbb39-c61b-4236-9ea7-f3ce4aeaac2e.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

In this example the step is given by a series of numbers

.. image:: https://user-images.githubusercontent.com/14288520/188505926-6df53a6f-c74c-42d3-b663-e5285e501729.png
  :target: https://user-images.githubusercontent.com/14288520/188505926-6df53a6f-c74c-42d3-b663-e5285e501729.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

You can create multiple lines if input multiple lists

.. image:: https://user-images.githubusercontent.com/14288520/188505934-2d16c5e3-7392-40ab-9a84-6c8e91bda75a.png
  :target: https://user-images.githubusercontent.com/14288520/188505934-2d16c5e3-7392-40ab-9a84-6c8e91bda75a.png

* Number-> :doc:`List Input </nodes/number/list_input>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

---------

The "OD" mode (Origin Direction) can be used to visualize normals

.. image:: https://user-images.githubusercontent.com/14288520/188507605-ffcd79cf-498d-4fcd-8ac1-a5f7966aacd0.png
  :target: https://user-images.githubusercontent.com/14288520/188507605-ffcd79cf-498d-4fcd-8ac1-a5f7966aacd0.png

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Analyzers-> :ref:`Component Analyzer/Faces/Center <FACES_CENTER>`
* Analyzers-> :ref:`Component Analyzer/Faces/Normal <FACES_NORMAL>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`