Taper Field
===========

Functionality
-------------

This node generates a Vector Field, which does Taper (conical) transformation
of some region of space.

Taper transformation requires some axis and a point on this axis, where all
lines that were parallel to axis will intersect. We call that point Vertex.

Inputs
------

This node has the following inputs:

* **Point**. A point on taper axis. This is used along with Vertex input to
  define taper axis. The default value is ``(0, 0, 0)``.
* **Vertex**. Taper vertex - the point where all lines which were parallel to
  taper axis should intersect. The default value is ``(0, 0, 1)``.
* **MinZ**, **MaxZ**. These inputs are only available when **Use Min Z** /
  **Use Max Z** parameters are checked. They define the range of space along
  taper axis, which is to be transformed. Z value of zero corresponds to the
  level where point defined in the **Point** input is. Z value of 1.0
  corresponds to the level where taper vertex is. The default values are
  **MinZ** = 0, **MaxZ** = 1.

Parameters
----------

This node has the following paramters:

* **Use Min Z**, **Use Max Z**. Indicate whether it is required to restrict
  taper transformation to a region of space along taper axis. Unchecked by
  default, so by default the transformation is applied to whole space.

Outputs
-------

This node has the following outputs:

* **Field**. The generated vector field.

Examples of Usage
-----------------

Simple example:

.. image:: https://github.com/user-attachments/assets/7238097d-8f7c-4ed4-80f8-1d2cdfbc466c
  :target: https://github.com/user-attachments/assets/7238097d-8f7c-4ed4-80f8-1d2cdfbc466c

Example where taper vertex is visible:

.. image:: https://github.com/user-attachments/assets/1cc1eb9d-7671-4ade-a63f-3edc9b52a5ff
  :target: https://github.com/user-attachments/assets/1cc1eb9d-7671-4ade-a63f-3edc9b52a5ff

Example of restricted taper transformation:

.. image:: https://github.com/user-attachments/assets/3cc36191-c5f2-49ca-9997-7a511b2790e4
  :target: https://github.com/user-attachments/assets/3cc36191-c5f2-49ca-9997-7a511b2790e4

