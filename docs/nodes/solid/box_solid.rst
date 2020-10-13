Box (Solid)
===========

Functionality
-------------

Offers a Solid Box primitive with variable Length, Width and Height.

Parameters
----------

This node has the following parameter:

- Origin type. This determines which point of the box is defined by "Origin"
  input (in case Direction is set to `(0,0,1)`). The available options are:

  * Corner. "Origin" input will define the location of "left-down-nearer"
    corner of the box, i.e. the corner with the smallest values of X, Y, and Z
    coordinates.
  * Center. "Origin" input will define the location of central point of the box.
  * Bottom. "Origin" input will define the location of the center of box's bottom face.
  
  The default option is Corner.

Inputs
------

All inputs are vectorized and the data will be matched to the longest list

- Length: Size of the Box along the X axis.
- Width: Size of the Box along the Y axis.
- Height: Size of the Box along the Z axis..
- Origin: Position of the box (Bottom left corner).
- Direction: Orientation of the box (Z axis of the box). Note that changing
  this input from default `(0,0,1)` will rotate the box around it's corner with
  smallest values of X,Y,Z coordinate, regardles of the "Origin type"
  parameter.

Outputs
-------

- Solid


Examples
--------

.. image:: https://raw.githubusercontent.com/vicdoval/sverchok/docs_images/images_for_docs/solid/box_solid/box_solid_blender_sverchok_example.png
