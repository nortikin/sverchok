Line
====

.. image:: https://user-images.githubusercontent.com/28003269/72215538-0f04e180-352d-11ea-8db3-0a9493ff54e2.png

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

+---------------+---------------+--------------+---------------------------------------------------------+
| Param         | Type          | Default      | Description                                             |
+===============+===============+==============+=========================================================+
| **Direction** | Enum          | "X"          | Ortho direction "Origin and point on line"              | 
|               |               |              |                 or "Origin and Direction"               |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Length**    | Enum          | "Size"       | Method of line size determination                       |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Center**    | Boolean       | False        | center line in origin                                   |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Split to    | Boolean       |              |                                                         |
| objects**     | (N panel)     | True         | Each line will be put to separate object any way        |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Numpy       | Boolean       | False        | Convert vertices to Numpy array                         |
| output**      | (N panel)     |              |                                                         |
+---------------+---------------+--------------+---------------------------------------------------------+

**Step length mode** - expect array of steps with help of which a line can be subdivided into unequal parts.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/28003269/72215709-25f90300-3530-11ea-8e5d-4f2c184cbfd5.png
  :alt: LineDemo1.PNG

The first example shows just an standard line with 5 vertices and 1.00 ud between them

.. image:: https://user-images.githubusercontent.com/28003269/72215740-87b96d00-3530-11ea-968d-c5acda2db0a6.png
  :alt: LineDemo2.PNG

In this example the step is given by a series of numbers

.. image:: https://user-images.githubusercontent.com/28003269/72215766-fa2a4d00-3530-11ea-8363-9f18f4122d8c.png
  :alt: LineDemo3.PNG  

You can create multiple lines if input multiple lists

.. image:: https://user-images.githubusercontent.com/28003269/72215798-9b190800-3531-11ea-923b-add9e4dc0966.png
  :alt: LineDemo5.PNG 

The "OD" mode can be used to visualize normals