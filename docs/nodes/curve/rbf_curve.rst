RBF Curve
=========

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Curve, based on provided points, by use of RBF_ method.
Depending on node parameters, the curve can be either interpolating (go through
all points) or only approximating.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function

Inputs
------

This node has the following inputs:

* **Vertices**. The points to build the curve for. This input is mandatory.
* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated curve. The default value is 1.0.
* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the curve will go through all provided points; otherwise, it will be only an
  approximating curve. The default value is 1.0.

Parameters
----------

This node has the following parameter:

* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

  The default function is Multi Quadric.

Outputs
-------

This node has the following output:

* **Curve**. The generated Curve object.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87217900-a70e4700-c367-11ea-8deb-1a9ebc664632.png

