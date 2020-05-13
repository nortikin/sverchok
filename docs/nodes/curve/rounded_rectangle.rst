Rounded Rectangle
=================

Functionality
-------------

This node generates a Curve object, which represents a rectangle with rounded corners.

Inputs
------

This node has the following inputs:

* **Size X**. Size of the rectangle along the X axis (rectangle width). The default value is 10.
* **Size Y**. Size of the rectangle along the Y axis (rectangle height). The default value is 10.
* **Radius**. Corner rounding radius. This input can consume lists of nesting
  level 2 or 3. If the input data have nesting level 3, then it is supposed
  that the input defines seprate radius for each of 4 corners of each
  rectangle. If the radius is zero, then there will be no rounding arc
  generated at the corresponding corner of the rectangle. The default value is
  1.0.

Parameters
----------

This node has the following parameters:

* **Center**. If checked, then the generated curve will be centered around
  world's origin; in other words, the center of the rectangle will be at ``(0,
  0, 0)``. If not checked, the left-down corner of the rectangle will be at the
  origin. Unchecked by default.
* **Even domains**. If checked, give each segment a domain of length 1.
  Otherwise, each arc will have a domain of length ``pi/2``, and each straight
  line segment will have a domain of length equal to the segment's length.
  Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Curve**. The generated Curve object. The curve always lies in the XOY plane.
* **Centers**. Center points of generated arc segments.

Examples of usage
-----------------

Simple example:

.. image:: https://user-images.githubusercontent.com/284644/81508400-5f465180-931d-11ea-9ce7-95b69c2e4925.png

Vectorization example 1 - sizes only:

.. image:: https://user-images.githubusercontent.com/284644/81509449-3d040200-9324-11ea-9b31-504633b880b4.png

Vectorization example 2 - sizes and radiuses per rectangle:

.. image:: https://user-images.githubusercontent.com/284644/81509502-9c621200-9324-11ea-92a7-4d3d46f01c7e.png

Vectorization example 3 - sizes and radiuses per rectangle corner:

.. image:: https://user-images.githubusercontent.com/284644/81509473-60c74800-9324-11ea-8c92-48b3d427727d.png

