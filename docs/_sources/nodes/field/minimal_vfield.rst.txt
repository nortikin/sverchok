RBF Vector Field
================

Dependencies
------------

This node optionally uses SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Vector Field for given set of points in 3D space and
corresponding vector field values (vectors), by use of RBF_ method. Depending
on node parameters, the field can be interpolating, i.e. have exactly the
provided values in the provided points, or only approximating.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function

Inputs
------

This node has the following inputs:

* **VerticesFrom**. The set of points where the values of the vector field are
  known. This input is mandatory.
* **VerticesTo**. The values of the vector field (i.e. vectors) in points
  defined by **VerticesFrom** input. This input is mandatory.
* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated field. The default value is 1.0.
* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the field will have exactly the specified values in all provided points;
  otherwise, it will be only an approximating field. The default value is 0.0.

Parameters
----------

This node has the following parameters:

* **Field type**. The available options are:

  * **Relative**. The node will output a "relative" vector field, i.e. it will
    be supposed to work with "Apply vector field" node. The vectors in
    **VerticesTo** input are supposed to be "force vectors", i.e. vectors that
    should be added to points in **VectorsFrom** input.
  * **Absolute**. The node will output an "absolute" vector field, i.e. it will
    be supposed to work with "Evaluate vector field" node. The vectors in
    **VerticesTo** input are supposed to be points where points from
    **VerticesFrom** input should be mapped to.

  The default option is **Relative**.

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

* **Field**. The generated vector field.

Example of usage
----------------

Define eight "force" vectors for each of eight vertices of a cube. Build an interpolating vector field for such vectors. Then apply it to better subdivided cube:

.. image:: https://user-images.githubusercontent.com/284644/87243779-19f3ec80-c452-11ea-8570-b95db6e11efb.png

