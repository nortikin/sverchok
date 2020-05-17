Center
======

Functionality
-------------

This node centers the input vertices around world origin. It also outputs the average of the inputted vertices.

The center is interpreted as the mean of the vectors not the center of mass

Inputs & Parameters
-------------------

+-----------------+---------+------------------------------------------------------------------------------+
| Name            | Type    | Description                                                                  |
+=================+=========+==============================================================================+
| Center of many  | Boolean | Determine if center each object (Level 3) or each group of objects (Level 4) |
+-----------------+----------------------------------------------------------------------------------------+
| Vertices        | Vectors | Represents vertices or intermediate vectors used for further vector math     |
+-----------------+----------------------------------------------------------------------------------------+

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

** Implementation**: NumPy or Python. (Default NumPy) NumPy will be faster on larger lists or when dealing with numpy arrays.

**Output NumPy**: Output NumPy arrays in stead of regular lists (makes the node faster) (Only in NumPy implementation)

Outputs
-------

**Vertices** The list of vertices centered around origin.

**Center**: The mean of input list(s)


Examples
--------

Centering a random polygon:

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/transforms/center/center_sverchok_blender_example_1.png

Difference between enabling "Center of many"
.. image:: https://cloud.githubusercontent.com/assets/619340/4186411/a3e1c14a-3760-11e4-84fe-2acaf1858ad7.PNG
