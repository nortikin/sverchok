Circle
======

.. image:: https://user-images.githubusercontent.com/14288520/188688493-18413b57-3f2e-49e6-8bbf-840a34a93b19.png
  :target: https://user-images.githubusercontent.com/14288520/188688493-18413b57-3f2e-49e6-8bbf-840a34a93b19.png

Functionality
-------------

Circle generator creates circles based on the radius and the number of vertices. A higher number of verts gives a more detailed approximation of a circle::

    - 3 vertices = triangle.
    - 4 vertices = square
    - ...
    - 6 vertices =  hexagon
    - ...
    - Many vertices =  circle

This node will also create sector or segment of a circle using the **Degrees** option. See the examples below to see it working also with the **mode** option.

.. image:: https://user-images.githubusercontent.com/14288520/191244809-264cf486-eb00-4399-921b-b7f685551bd0.png
  :target: https://user-images.githubusercontent.com/14288520/191244809-264cf486-eb00-4399-921b-b7f685551bd0.png

Inputs
------

All inputs are vectorized and they will accept single or multiple values.
There are three inputs:

- **Radius**
- **N Vertices**
- **Degrees**

Same as other generators, all inputs will accept a single number, an array or even an array of arrays::

    [2]
    [2, 4, 6]
    [[2], [4]]

Parameters
----------

All parameters except **Mode** can be given by the node or an external input.


+----------------+---------------+-------------+----------------------------------------------------+
| Param          | Type          | Default     | Description                                        |
+================+===============+=============+====================================================+
| **Radius**     | Float         | 1.00        | radius of the circle                               |
+----------------+---------------+-------------+----------------------------------------------------+
| **N Vertices** | Int           | 24          | number of vertices to generate the circle          |
+----------------+---------------+-------------+----------------------------------------------------+
| **Degrees**    | Float         | 360.0       | angle for a sector/segment circle                  |
+----------------+---------------+-------------+----------------------------------------------------+
| **Mode**       | Boolean       | False       | switch between two sector and segment circle       |
+----------------+---------------+-------------+----------------------------------------------------+

Outputs
-------

**Vertices**, **Edges** and **Polygons**. 
All outputs will be generated. Depending on the type of the inputs, the node will generate only one or multiple independent circles. In example:

.. image:: https://cloud.githubusercontent.com/assets/5990821/4187227/07366302-3768-11e4-8e9c-4068c9ce6773.png
  :target: https://cloud.githubusercontent.com/assets/5990821/4187227/07366302-3768-11e4-8e9c-4068c9ce6773.png
  :alt: CircleDemo1.PNG

.. image:: https://cloud.githubusercontent.com/assets/5990821/4187228/0759a754-3768-11e4-80a4-458e286edf20.png
  :target: https://cloud.githubusercontent.com/assets/5990821/4187228/0759a754-3768-11e4-80a4-458e286edf20.png
  :alt: CircleDemo2.PNG

As you can see in the red rounded values, depending on how many data inputs the node has, will be generated those same number of outputs.

If **Degrees** is less than 360, depending of the **mode** state, the node generates a sector or a segment of a circle of the given number of degrees.

Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5990821/4186877/ab2f2e98-3764-11e4-9cd6-502228eec31c.png
  :target: https://cloud.githubusercontent.com/assets/5990821/4186877/ab2f2e98-3764-11e4-9cd6-502228eec31c.png
  :alt: CircleDemo3.PNG

In this first example we see that circle generator can be a circle but also any regular polygon that you want.

.. image:: https://cloud.githubusercontent.com/assets/5990821/4186876/ab2edf4c-3764-11e4-980e-d9beb10b16d8.png
  :target: https://cloud.githubusercontent.com/assets/5990821/4186876/ab2edf4c-3764-11e4-980e-d9beb10b16d8.png
  :alt: CircleDemo4.PNG

The second example shows the use of **mode** option and how it generates sector or segment of a circle based on the **degrees** value.
