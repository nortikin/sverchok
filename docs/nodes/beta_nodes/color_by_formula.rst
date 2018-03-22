Color by formula
========

Functionality
-------------

available variables: **r**, **g**, **b**, **a** for access to initial colors from first input socket. If second input color socket is connected, **R**, **G**, **B**, **A**
variables can be used to access its values.
And **i** for access to index of current color to be evaluated. It is also possible
to get index of current object list of colors evaluated as **I** variable.
So **i** for index of color, and **I** for index of list of colors.
Internally imported everything from Python **math** module.
Blender Py API also accessible (like **bpy.context.scene.frame_current**)

Inputs
------

- **Colors(rgba)**
- **Colors(RGBA)**

Outputs
-------

**Colors**.
resulted colors to red, green, blue and alpha elements of which was applied expression.

Example of usage
----------------
.. image:: https://user-images.githubusercontent.com/22656834/37774133-44806c24-2e01-11e8-85ba-361a18315ff9.png
