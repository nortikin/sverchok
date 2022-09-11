Elevate Degree (NURBS Surface)
==============================

Functionality
-------------

This node elevates (increases) the degree of a NURBS surface.

The opposite action can be performed with "Reduce Degree (NURBS Surface)" node.

Surfaces of higher degrees have more control points, and so, with higher degree,
one control point controls smaller segment of the surface.

Remember that NURBS surface has two degrees, one along U parameter and one
along V. This node can elevate any of them.

This node can work only with NURBS and NURBS-like surfaces.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to perform operation on. This input is mandatory.
* **Degree**. In **Elevate by** mode, this is the delta to be added to surface's
  degree. In **Set degree** mode, this is new surface degree to be set. New
  degree can not be less than current degree of the surface. The default value is
  1.

Parameters
----------

This node has the following parameters:

* **Direction**. This specifies the parameter direction, degree along which is
  to be increased. The available options are **U** and **V**. The default
  option is **U**.
* **Mode**. This defines how the new degree of the surface is specified:

  * In **Elevate by** mode, **Degree** input specifies the number to be added
    to current degree of the surface.
  * In **Set degree** mode, **Degree** input specifies the new degree of the
    surface.

Outputs
-------

This node has the following output:

* **Surface**. The surface of elevated degree.

Example of Usage
----------------

Here the degree of the surface is increased by 1 along U and then reduced by 1
also along U, just to illustrate that degree elevation and reduction are the
opposite processes. Red is the control net of the original and the resulting
surfaces. Blue is the control polygon of degree elevated surface.

.. image:: https://user-images.githubusercontent.com/284644/189500531-e4354c9d-0dd4-4bc5-861d-43d9229c28e6.png

