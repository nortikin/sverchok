Reduce Degree (NURBS Surface)
=============================

Functionality
-------------

This node reduces (decreases) the degree of a NURBS surface.

The action of this node is the opposite to the action of "Elevate Degree (NURBS Surface)" node.

Degree reduction is the process which can not be always performed exactly. Some
surfaces can not be degree reduced without visible deviation of surface's geometry.
For other, degree reduction produces only small error.

Remember that NURBS surface has two degrees, one along U parameter and one
along V. This node can reduce any of them.

This node can work only with NURBS and NURBS-like surfaces.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to perform operation on. This input is mandatory.
* **Degree**. In **Reduce by** mode, this is the delta to be substracted from
  surface's degree. In **Set degree** mode, this is new surface degree to be
  set. New degree can not be greater than current degree of the surface. The
  default value is 1.
* **Tolerance**. Maximum tolerable deviation of new surface from original. If
  degree reduction process will have error estimation more than this tolerance,
  then, depending on **Only if possible** parameter, the node will either fail or
  return the surface untouched (or degree reduced by less than wanted value). The
  default value is ``0.0001``.

Parameters
----------

This node has the following parameters:

* **Direction**. This specifies the parameter direction, degree along which is
  to be decreased. The available options are **U** and **V**. The default
  option is **U**.
* **Mode**. This defines how the new degree of the surface is specified:

  * In **Reduce by** mode, **Degree** input specifies the number to be
    substracted from current degree of the surface.
  * In **Set degree** mode, **Degree** input specifies the new degree of the
    surface.

Outputs
-------

This node has the following output:

* **Surface**. The surface of a reduced degree.

Example of Usage
----------------

Here the degree of the surface is increased by 1 along U and then reduced by 1
also along U, just to illustrate that degree elevation and reduction are the
opposite processes. Red is the control net of the original and the resulting
surfaces. Blue is the control polygon of degree elevated surface.

.. image:: https://user-images.githubusercontent.com/284644/189500531-e4354c9d-0dd4-4bc5-861d-43d9229c28e6.png

