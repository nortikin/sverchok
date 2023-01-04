Single-Point Curve
==================

Functionality
-------------

This node generates a trivial curve, which consists of only one point in 3D
space. Such a curve is not useful by itself, but it can be useful in
combination with nodes which use curves to make some more complex construction.
For example, it is possible to do a loft with a single-point curve.

Inputs
------

This node has the following input:

* **Point**. The point which will become the Curve object. The default value is (0, 0, 0).

Parameters
----------

This node does not have parameters.

Outputs
-------

This node has the following output:

* **Curve**. The generated Curve object.

Examples of Usage
-----------------

Use with "Blend Curves" node to construct a smooth continuation of given curve, which ends in a specific point:

.. image:: https://user-images.githubusercontent.com/284644/210247639-1352bd93-10a4-4145-97de-2f770afa368a.png
  :target: https://user-images.githubusercontent.com/284644/210247639-1352bd93-10a4-4145-97de-2f770afa368a.png

Use with "NURBS Loft" node, to construct a surface which has "poles":

.. image:: https://user-images.githubusercontent.com/284644/210247716-70957dc2-6495-4067-ae1f-6ae0f0c3e9b9.png
  :target: https://user-images.githubusercontent.com/284644/210247716-70957dc2-6495-4067-ae1f-6ae0f0c3e9b9.png

