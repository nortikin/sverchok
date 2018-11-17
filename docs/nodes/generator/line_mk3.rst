Line
====

Functionality
-------------

Line generator creates a series of connected segments based on the number of vertices and the length between them. Just a standard subdivided line along X axis

Inputs
------

All parameters except **Center** are vectorized. They will accept single or multiple values.
Both inputs will accept a single number or an array of them. It also will work an array of arrays::

    [2]
    [2, 4, 6]
    [[2], [4]]

Parameters
----------

All parameters except **Center** can be given by the node or an external input.


+---------------+---------------+--------------+---------------------------------------------------------+
| Param         | Type          | Default      | Description                                             |
+===============+===============+==============+=========================================================+
| **Direction** | Enum          | "X"          | Ortho direction, "from A to B" or "Origin and Direction"|
+---------------+---------------+--------------+---------------------------------------------------------+
| **N Verts**   | Int           | 2            | number of vertices. The minimum is 2                    |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Step**      | Float         | 1.00         | length between vertices                                 |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Center**    | Boolean       | False        | center line around 0                                    |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Normalize** | Boolean       | False        | determine steps by fixing total length line             |
+---------------+---------------+--------------+---------------------------------------------------------+
| **Size**      | Float         | 10           | total length of the segment                             |
+---------------+---------------+--------------+---------------------------------------------------------+
| **A, O**      | Vector        | (0,0,0)      | origin point of line                                    |
+---------------+---------------+--------------+---------------------------------------------------------+
| **B**         | Vector        | (0.5,0.5,0.5)| end point of line                                       |
+---------------+---------------+--------------+---------------------------------------------------------+
| **D**         | Vector        | (1,1,1)      | direction of the line                                   |
+---------------+---------------+--------------+---------------------------------------------------------+

Outputs
-------

**Vertices** and **Edges**. Verts and Edges will be generated. Depending on the inputs, the node will generate only one or multiples independent lines. See examples below.


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