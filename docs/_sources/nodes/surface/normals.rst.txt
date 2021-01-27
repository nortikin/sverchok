Surface Frame
=============

Functionality
-------------

This node outputs information about normals and tangents of the surface at
given points, together with a matrix giving reference frame according to
surface normals.

Inputs
------

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

This node has the following outputs:

* **Normal**. Unit normal vectors of the surface at the specified points.
* **TangentU**. Unit tangent vectors of the surface at the specified points
  along the U direction; more precisely, if the surface is defined by ``P =
  F(u, v)``, then this is ``dF/du`` vector divided by it's length.
* **TangentV**. Unit tangent vectors of the surface at the specified points
  along the V direction; more precisely, if the surface is defined by ``P =
  F(u, v)``, then this is ``dF/dv`` vector divided by it's length.
* **AreaStretch**. Coefficient of the stretching of the surface area in the
  mapping of areas in the UV space to 3D space, in the provided points. This
  equals to ``|dF/du| * |dF/dv|`` (norm of derivative by U multiplied by norm
  of derivative by V). So, **AreaStretch** is always equal to product of
  **StretchU** by **StretchV**.
* **StretchU**. Coefficient of stretching the surface along the U direction;
  this equals to ``|dF/du|``.
* **StretchV**. Coefficient of stretching the surface along the V direction;
  this equals to ``|dF/dv|``.
* **Matrix**. Reference frame at the surface point, defined by the surface's
  normal and parametric tangents: it's Z axis is looking along surface normal;
  it's X axis is looking along **TangentU**, and it's Y axis is looking along
  **TangentV**.

Examples of Usage
-----------------

Visualize Matrix outputfor some formula-defined surface:

.. image:: https://user-images.githubusercontent.com/284644/81722587-06042c80-949b-11ea-81a4-43d134c9ca77.png

Use that matrices to place cubes, oriented accordingly:

.. image:: https://user-images.githubusercontent.com/284644/81722585-056b9600-949b-11ea-9ad9-01f7093c9c80.png

As you can see, the surface in areas that are far from the center, so that cubes are put sparsely. Let's use StretchU and StretchV outputs to scale them:

.. image:: https://user-images.githubusercontent.com/284644/81722582-03a1d280-949b-11ea-8e99-9d9354f5e906.png

