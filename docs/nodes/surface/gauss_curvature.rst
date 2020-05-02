Surface Gauss Curvature
=======================

Functionality
-------------

This node calculates the Gaussian curvature (see Wikipedia_ article) at the specified point of the surface.

.. _Wikipedia: https://en.wikipedia.org/wiki/Gaussian_curvature

Here are the main facts about Gaussian curvature that are usually useful:

* For points where the surface is shaped like sphere, Gaussian curvature is positive;
* For "saddle points" of the surface, Gaussian curvature is negative;
* If the surface is "flat" at the given point in one or two directions, then Gaussian curvature is zero;
* The more "bent" the surface is at the given point is, the bigger the absolute value of Gaussian curvature will be.

Note that the calculation is done by numerical differentiation, so it may be not very precise in some cases.

Inputs
------

This node has the following inputs:

* **Surface**. The surface to analyze. This input is mandatory.
* **U**, **V**. Values of U and V surface parameters. These inputs are
  available only when **Input mode** parameter isset to **Separate**. The
  default value is 0.5.
* **UVPoints**. Points at which the surface is to be analyzed. Only two of
  three coordinates will be used; the coordinates used are defined by the
  **Orientation** parameter. This input is available and mandatory if the
  **Input mode** parameter is set to **Vertices**.

Parameters
----------

This node has the following parameters:

* **Input mode**. The available options are:

   * **Separate**. The values of U and V surface parameters will be provided in
     **U** and **V** inputs, correspondingly.
   * **Vertices**. The values of U and V surface parameters will be provided in
     **Vertices** input; only two of three coordinates of the input vertices
     will be used.
   
   The default mode is **Separate**.

* **Input orientation**. This parameter is available only when  **Input mode**
  parameter is set to **Vertices**. This defines which coordinates of vertices
  provided in the **Vertices** input will be used. The available options are
  XY, YZ and XZ. For example, if this is set to XY, then the X coordinate of
  vertices will be used as surface U parameter, and Y coordinate will be used
  as V parameter. The default value is XY.
* **Clamp**. This defines how the node will process the values of
  surface U and V parameters which are out of the surface's domain. The
  available options are:

   * **As is**. Do not do anything special, just pass the parameters to the
     surface calculation algorithm as they are. The behaviour of the surface
     when the values of parameters provided are out of domain depends on
     specific surface: some will just calculate points by the same formula,
     others will give an error.
   * **Clamp**. Restrict the parameter values to the surface domain: replace
     values that are greater than the higher bound with higher bound value,
     replace values that are smaller than the lower bound with the lower bound
     value. For example, if the surface domain along U direction is `[0 .. 1]`,
     and the value of U parameter is 1.05, calculate the point of the surface
     at U = 1.0.
   * **Wrap**. Wrap the parameter values to be within the surface domain, i.e.
     take the values modulo domain. For example, if the surface domain along U
     direction is `[0 .. 1]`, and the value of U parameter is 1.05, evaluate
     the surface at U = 0.05.

   The default mode is **As is**.

Outputs
-------

This node has the following output:

* **Curvature**. The calculated curvature value.

Examples of usage
-----------------

Gaussian curvature of plane is zero at any point:

.. image:: https://user-images.githubusercontent.com/284644/80866465-3e8c5500-8ca8-11ea-88de-01b281f3b608.png

Gaussian curvature of sphere of the radius R is `1/R^2` at any point:

.. image:: https://user-images.githubusercontent.com/284644/80866466-3fbd8200-8ca8-11ea-94ff-627e0215cdd8.png

Use Gaussian curvature to color vertices of toroidal surface (yellowish for positive curvature, black for negative):

.. image:: https://user-images.githubusercontent.com/284644/80866468-40561880-8ca8-11ea-8504-752c07f19879.png

Similar for another formula-defined surface (purple for positive curvature, yellow for negative, cyan for nearly zero):

.. image:: https://user-images.githubusercontent.com/284644/80866603-03d6ec80-8ca9-11ea-8d00-60e48e4a1f85.png

