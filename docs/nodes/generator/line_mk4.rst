Line
====

Functionality
-------------

Line generator creates a series of connected segments based on the number of vertices and the length between them.

Inputs
------

All parameters except **Center**, **Mode** and **Normalize** are vectorized. They will accept single or multiple values. The **Num Verts**, **Steps** and **Size** inputs will accept a single number, an array of numbers or an array of array of numbers, e.g.

    [[2]]
    [[2, 4, 6]]
    [[2], [4], [6]]

Parameters
----------

All parameters except **Center**, **Mode** and **Normalize** can be given by the node or an external input.

+---------------+-----------+-----------+--------------------------------------------------------+
| Param         | Type      | Default   | Description                                            |
+===============+===========+===========+========================================================+
| **Mode**      | Enum      | "OD"      | The line direction mode:                               |
|               |           |           |  AB : create line from point A to point B              |
|               |           |           |  OD : create line from origin O, along direction D     |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Num Verts** | Int       | 2         | The number of vertices in the line. [1]                |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Step**      | Float     | 1.00      | The length between vertices. [2]                       |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Center**    | Boolean   | False     | Center the line around its starting point location.    |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Normalize** | Boolean   | False     | Normalize the line length to the given line size.      |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Size**      | Float     | 10.00     | The length of the normalized line. [3]                 |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Point A**   | Vector    | (0,0,0)   | The starting point of the line. [4]                    |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Point B**   | Vector    | (1,0,0)   | The ending point of the line. [4]                      |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Origin**    | Vector    | (0,0,0)   | The origin of the line. [5]                            |
+---------------+-----------+-----------+--------------------------------------------------------+
| **Direction** | Vector    | (1,0,0)   | The direction of the line. [5]                         |
+---------------+-----------+-----------+--------------------------------------------------------+

Notes:
[1] : The minimum number of vertices is 2.
[2] : The number of steps is limited by the Num Verts
[3] : The "Size" input socket is only visible when the "Normalize" flag is enabled.
[4] : Point A and Point B are displayed in AB mode
[5] : Origin and Direction are displayed in OD mode

Outputs
-------

**Vertices** and **Edges** will be generated when the output sockets are connected. Depending on the inputs, the node will generate one or multiples independent lines. See examples below.

Presets
-------
The node provides a set of predefined line directions along X, Y and Z. These buttons will set the mode to **OD**, the **Origin** to (0,0,0) and the **Direction** to one of the X, Y or Z directions: (1,0,0), (0,1,0) and (0,0,1) respectively. The preset buttons are only visible as long as the Point B or Direction input socket is not connected.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/10011941/47713459-a177d880-dc3a-11e8-935b-a2fa494dc49b.png
  :alt: LineDemo1.PNG

The first example shows just an standard line with 5 vertices and 1.00 ud between them

.. image:: https://user-images.githubusercontent.com/10011941/47713473-a9377d00-dc3a-11e8-94ab-39095761788c.png
  :alt: LineDemo2.PNG

In this example the step is given by a series of numbers

.. image:: https://user-images.githubusercontent.com/10011941/47713477-ad639a80-dc3a-11e8-9884-6568326d2a33.png
  :alt: LineDemo3.PNG

You can create multiple lines if input multiple lists

.. image:: https://user-images.githubusercontent.com/10011941/47713487-b3597b80-dc3a-11e8-996b-17edf1cec9da.png
  :alt: LineDemo4.PNG

The AB mode will output a divided segment for each vector pair, the step can be used to change the proportions of the divisions

.. image:: https://user-images.githubusercontent.com/10011941/47713488-b3597b80-dc3a-11e8-9e6e-f742d0338ba5.png
  :alt: LineDemo5.PNG

The "OD" mode can be used to visualize normals

.. image:: https://user-images.githubusercontent.com/10011941/47713490-b3597b80-dc3a-11e8-9b6d-b937c0375ec5.png
  :alt: LineDemo5.PNG

Advanced example using the node to create a paraboloid grid