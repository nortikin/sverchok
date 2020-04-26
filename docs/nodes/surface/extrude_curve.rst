Extrude Curve Along Curve
=========================

Functionality
-------------

This node generates a Surface object by extruding one Curve (called "profile") along another Curve (called "Extrusion").
The Profile curve may optionally be rotated while extruding, to make result look more naturally.

It is supposed that the profile curve is positioned so that it's "logical
center" (i.e., the point, which is to be moved along the extrusion curve) is
located at the global origin `(0, 0, 0)`.

Surface domain: Along U direction - the same as of "profile" curve; along V
direction - the same as of "extrusion" curve.

Inputs
------

This node has the following inputs:

* **Profile**. The profile curve (one which is to be extruded). This input is mandatory.
* **Extrusion**. The extrusion curve (the curve along which the profile is to be extruded). This input is mandatory.
* **Resolution**. Number of samples for **Zero-Twist** rotation algorithm
  calculation. The more the number is, the more precise the calculation is, but
  the slower. The default value is 50. This input is only available when
  **Algorithm** parameter is set to **Zero-Twist**.

Parameters
----------

This node has the following parameters:

* **Algorithm**. Profile curve rotation calculation algorithm. The available options are:

  * **None**. Do not rotate the profile curve, just extrude it as it is. This mode is the default one.
  * **Frenet**. Rotate the profile curve according to Frenet frame of the extrusion curve.
  * **Zero-Twist**. Rotate the profile curve according to "zero-twist" frame of the extrusion curve.
  * Householder: calculate rotation by using Householder's reflection matrix
    (see Wikipedia_ article).                   
  * Tracking: use the same algorithm as in Blender's "TrackTo" kinematic
    constraint. This node currently always uses X as the Up axis.
  * Rotation difference: calculate rotation as rotation difference between two
    vectors.                                         

* **Origin**. This parameter defines the position of the resulting surface with
  relation to the positions of the profile curve and the extrusion curve. It is
  useful when the beginning of the extrusion curve does not coincide with
  global origin `(0, 0, 0)`. The available options are:

   * **Global origin**. The beginning of the surface will be placed at global origin.
   * **Extrusion origin**. The beginning of the surface will be placed at the beginning of the extrusion curve.
   
  The default option is **Global origin**.

.. _Wikipedia: https://en.wikipedia.org/wiki/QR_decomposition#Using_Householder_reflections

Outputs
-------

This node has the following output:

* **Surface**. The generated surface.

Examples of usage
-----------------

"None" algorithm works fine in many simple cases:

.. image:: https://user-images.githubusercontent.com/284644/79357796-eb04d200-7f59-11ea-8ef1-cb35ebb0083e.png

It becomes not so good if the extrusion curve has some rotations:

.. image:: https://user-images.githubusercontent.com/284644/79357777-e5a78780-7f59-11ea-8f08-ba309965b67c.png

Similar case with "Frenet" algorithm:

.. image:: https://user-images.githubusercontent.com/284644/79357785-e809e180-7f59-11ea-976a-a2bc32388ee0.png

The same with "Zero-Twist" algorithm:

.. image:: https://user-images.githubusercontent.com/284644/79357791-e93b0e80-7f59-11ea-9f8f-e74e1eead4cb.png

