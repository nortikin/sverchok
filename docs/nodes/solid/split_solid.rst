Split Solid by Face
===================

Functionality
-------------

This node takes one Solid object and one or several Surfaces (or Solid Faces),
and generates several Solid objects, by cutting the initial Solid with the
surfaces. This is similar to what "Bisect" node does to mesh, but this node can
cut the Solid with arbitrary surface, not only with planes.

This node supports NURBS and NURBS-like surfaces only.

Inputs
------

This node has the following inputs:

* **Solid**. The solid object to be split. This input is mandatory.
* **SolidFace**. Solid Face or Surface object to be used to cut the object. The
  node can use a list of surfaces to cut one object. This input is mandatory.

Outputs
-------

This node has the following outputs:

* **Solids**. The generated Solids objects. The node produces a list of Solid
  objects from each Solid object in the input.

Examples of Usage
-----------------

Take a cylinder and cut it with a surface generated from Bezier curve:

.. image:: https://user-images.githubusercontent.com/284644/92305529-9f52d380-efa1-11ea-9cbd-763e9a68d10b.png

Take one cube and cut it with a series of spheres:

.. image:: https://user-images.githubusercontent.com/284644/92305531-a0840080-efa1-11ea-89d5-5e86340eaae8.png

