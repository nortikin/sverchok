Approximate NURBS Surface
=========================

Dependencies
------------

This node requires Geomdl_ and FreeCAD_ library to work.

.. _Geomdl: https://onurraufbingol.com/NURBS-Python/
.. _FreeCAD: https://www.freecad.org/

Functionality
-------------

This node builds a NURBS_ Surface object, which approximates the given set of
points, i.e. goes as close to them as possible while remaining a smooth surface.

In fact, the generated surface always will be a non-rational surface, which means
that all weights will be equal to 1.

To build a NURBS surface, one needs an array of M x N points (like "3
rows by 4 points"). There are two modes of providing this array supported:

* You can provide a list of lists of points for each surface;
* Or you can provide a flat list of points, and instruct the node to
  subdivide it into sublists of N points each.

.. _NURBS: https://en.wikipedia.org/wiki/Non-uniform_rational_B-spline

Inputs
------

This node has the following inputs:

* **Vertices**. Points to be approximated. Depending on **Input mode**
  parameter, it expects either list of lists of control points per surface, or
  a flat list of control points per surface. This input is mandatory.
* **USize**. This input is only available when **Input mode** parameter is set
  to **Single list**.  
  The number of control points in a row. The default value is 5.

Geomdl_ implementation specific inputs:

* **Degree U**, **Degree V**. Degree of the surface along U and V directions, correspondingly. The default value is 3.
* **PointsCntU**, **PointsCntV**. Number of control points to be used along U and V directions, correspondingly. 
  These inputs are available only when **Specify points count** parameter is checked. 
  Otherwise, the node will generate as many control points as it needs (which may be too many). 
  The default value for these inputs (when they are available) is 5.


FreeCAD_ implementation specific inputs:

* **Minimal Degree**. Minimal possible degree of the surface to be built. 
  Default value is 3.
* **Maximal Degree**. Maximal possible degree of the surface to be built. 
  Default value is 5.
* **Tolerance**. Maximal distance of the built surface from the init Vertices.
  Default value is 0.0001.
  
* **Length Weight**. Available only for the "Variational Smoothing" method. 
  Default value is 1.0.
* **Curvature Weight**. Available only for the "Variational Smoothing" method. 
  Default value is 1.0.
* **Torsion Weight**. Available only for the "Variational Smoothing" method. 
  Default value is 1.0.

Parameters
----------

This node has the following parameters:

* **Implementation**. Approximation algorithm implementation to be used. The available values are:

  * **Geomdl**. Use the implementation from Geomdl_ library. This is available only when Geomdl library is installed.
  * **FreeCAD**. Use the implementation from FreeCAD_ library. This is available only when FreeCAD library is installed.

  By default, the first available implementation is used.

* **Centripetal**. Available only for Geomdl_ implementation. This defines whether the node will use centripetal
  approximation method. Unchecked by default.
* **Input mode**. The available values are:

  * **Single list**. The node expects a flat list of points for each surface. It will be subdivided into rows according to **USize** input value.
  * **Separate Lists**. The node expects a list of lists of points for each surface.
 
* **Specify points count**. Available only for Greomdl implementation. If checked, then the node allows you to specify the
  number of control points to generate in **PointsCntU**, **PointsCntV** inputs. Unchecked by default.
  
* **Continuity**. Available only for the FreeCAD_ implementation. Desired internal smoothness of the result surface. The available values are:

  * **C0** : Only positional continuity.
  * **C1** : Continuity of the first derivative.
  * **C2** : Continuity of the second derivative.

* **Method**. Available only for the FreeCAD_ implementation. Approximation algorithm implementation to be used. The available values are:

  * **Parametrization**. This method offers a list of metrics for the parametrization.
  * **Variational smoothing**. This method uses three additional parameters - "Length Weight", "Curvature Weight" and "Torsion Weight". 
    (with this smoothing algorithm, continuity C1 requires "Maximal Degree" >= 3 and C2 requires "Maximal Degree" >=5)

* **Metric**. This parameter is available when **Implementation** parameter is set to **FreeCAD/Parametrization**. 
  It's the metric (the specific knot values) to be used for interpolation. The available options are:

  * **Euclidean** also known as Chord-Length or Distance metric. The parameters of the points are proportionate to the distances between them.
  * **Centripetal** The parameters of the points are proportionate to square roots of distances between them.
  * **Points** also known as Uniform metric. The parameters of the points are distributed uniformly. Just the number of the points from the beginning.

  The default value is Euclidean.

Outputs
-------

This node has the following outputs:

* **Surface**. The generated NURBS surface.
* **ControlPoints**. Control points of the generated NURBS surface.
* **KnotsU**, **KnotsV**. Knot vectors of the generated NURBS surface.

Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/284644/87575638-a3711c00-c6e9-11ea-86ed-9c49d80b0763.png

Example of the FreeCAD implementation using the Variational Smoothing method:

.. image:: https://user-images.githubusercontent.com/66558924/216582148-39b1f8c5-addf-4be9-aa2b-c3f04f7e3b96.jpg



