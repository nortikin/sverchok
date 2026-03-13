Minimal Surface
===============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/c3e19248-a6e2-4da9-8472-a64586053d15
  :target: https://github.com/nortikin/sverchok/assets/14288520/c3e19248-a6e2-4da9-8472-a64586053d15

Dependencies
------------

This node requires SciPy_ library to work.

.. _SciPy: https://scipy.org/

Functionality
-------------

This node generates a Surface, based on provided points, by use of RBF_ method.
Depending on node parameters, the curve can be either interpolating (go through
all points) or only approximating.

The generated surface is not, strictly speaking, guaranteed to be minimal_; but
in many simple cases it is close enough to the minimal.

This node, in general, searches for a surface as a mapping from (U, V)
coordinates to (X, Y, Z). In many simple cases, you will want to provide just a
list of points, and tell the node to use their X and Y coordinates as U and V.
So, the node will actually only have to find a function which maps (X, Y) to Z.
In other cases, you will want to provide a set of (X, Y, Z) points and a set of
corresponding (U, V) coordinate pairs.

.. _RBF: http://www.scholarpedia.org/article/Radial_basis_function
.. _minimal: https://en.wikipedia.org/wiki/Minimal_surface

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ce5e1ccd-b6cc-40aa-991e-1a65b047871c
  :target: https://github.com/nortikin/sverchok/assets/14288520/ce5e1ccd-b6cc-40aa-991e-1a65b047871c

.. image:: https://github.com/nortikin/sverchok/assets/14288520/0525d736-bf3a-4a86-8bb0-696ca2853a90
  :target: https://github.com/nortikin/sverchok/assets/14288520/0525d736-bf3a-4a86-8bb0-696ca2853a90

Inputs
------

This node has the following inputs:

* **Vertices**. The points to build minimal surface for. This input is mandatory.
* **Epsilon**. Epsilon parameter of used RBF function; it affects the shape of
  generated surface. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/28246c31-b9cf-4852-9cef-7d45e138f4b6
      :target: https://github.com/nortikin/sverchok/assets/14288520/28246c31-b9cf-4852-9cef-7d45e138f4b6

* **Smooth**. Smoothness parameter of used RBF function. If this is zero, then
  the surface will go through all provided points; otherwise, it will be only an
  approximating surface. The default value is 0.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/bd911e6a-9e61-479c-95fe-80c28fce7f90
      :target: https://github.com/nortikin/sverchok/assets/14288520/bd911e6a-9e61-479c-95fe-80c28fce7f90

* **SrcU**, **SrcV**. U and V coordinates for the points specified in the
  **Vertices** input. These inputs are available and mandatory if the **Surface
  type** is set to **UV -> XYZ**, and **Explicit source UV** parameter is
  checked.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/3eaac98b-a660-47c9-b464-1a40628e3365
      :target: https://github.com/nortikin/sverchok/assets/14288520/3eaac98b-a660-47c9-b464-1a40628e3365

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
    * A*SCALAR:  Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
    * Add: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
    * Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

      **SrcU, SrcV: XY->Z**

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/9cf71434-ce52-4efb-8139-d61880d817b8
        :target: https://github.com/nortikin/sverchok/assets/14288520/9cf71434-ce52-4efb-8139-d61880d817b8

      **SrcU, SrcV: YZ->X**

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/beb8986c-3ae4-4113-aaa8-4313899610a3
        :target: https://github.com/nortikin/sverchok/assets/14288520/beb8986c-3ae4-4113-aaa8-4313899610a3

      **SrcU, SrcV: ZX->Y**

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/d44d064d-f370-493d-864d-2b0afe5737c3
        :target: https://github.com/nortikin/sverchok/assets/14288520/d44d064d-f370-493d-864d-2b0afe5737c3

      **SrcU, SrcV: PHI,Z->XYZ**

        .. image:: https://github.com/nortikin/sverchok/assets/14288520/a96a8631-8f98-4f67-8adc-073ab5c7c707
          :target: https://github.com/nortikin/sverchok/assets/14288520/a96a8631-8f98-4f67-8adc-073ab5c7c707

        * Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
        * Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
        * Vector-> :doc:`Vector Polar Output </nodes/vector/vector_polar_out>`
        * Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
        * A*SCALAR, ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
        * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
        * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
        * Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

        .. image:: https://github.com/nortikin/sverchok/assets/14288520/cd2cef71-486f-4bc4-a445-086e250393c6
          :target: https://github.com/nortikin/sverchok/assets/14288520/cd2cef71-486f-4bc4-a445-086e250393c6

* **Matrix**. Matrix used to extract U and V coordinates out of XYZ points.
  This input is available only if the **Surface type** is set to **XY -> Z**.
  The default is identity matrix.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6407d876-665f-4c75-b7ec-2f04a2db36f8 
      :target: https://github.com/nortikin/sverchok/assets/14288520/6407d876-665f-4c75-b7ec-2f04a2db36f8

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
    * A*SCALAR, ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f78de07c-7973-4344-aaa7-59cc84807761
      :target: https://github.com/nortikin/sverchok/assets/14288520/f78de07c-7973-4344-aaa7-59cc84807761

  Align surface with object:

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/45eedf83-25a0-4f74-abdd-863dfcc7a6c9
      :target: https://github.com/nortikin/sverchok/assets/14288520/45eedf83-25a0-4f74-abdd-863dfcc7a6c9

    * Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
    * Vector-> :doc:`Vector Noise </nodes/vector/noise_mk3>`
    * A*SCALAR, ADD: Vector-> :doc:`Vector Math </nodes/vector/math_mk3>`
    * Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
    * Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/7afc5d0e-862d-4dd4-abdc-f2acacca1f22
        :target: https://github.com/nortikin/sverchok/assets/14288520/7afc5d0e-862d-4dd4-abdc-f2acacca1f22

Parameters
----------

This node has the following parameters:

* **Surface type**. This defines which type of function the node will try to find. The available values are:

  * **XY -> Z**. The node will search for a function, mapping (X, Y)
    coordinates to Z (or (X, Z) to Y, or (Y, Z) to X,depending on
    **Orientation** parameter). So, in this mode the node can generate only
    surfaces which have a single Z value for each pair of X and Y. X, Y, Z
    coordinates can be rotated according to the **Matrix** input.
  * **UV -> XYZ**. The node will search for a function, mapping arbitrary (U,
    V) coordinates to (X, Y, Z). This mode is more general, but requires to
    pass U and V coordinate for each point somehow.

  The default option is **XY -> Z**.

* **Orientation**. This parameter is available only if **Surface type**
  parameter is set to **XY -> Z**. This defines which axis will be used as
  "function value". Other two axes will be used as U and V parameters. The
  available values are X, Y and Z. The default option is Z.
* **Explicit source UV**. This parameter is available only if **Surface type**
  parameter is set to **UV -> XYZ**. This defines whether you want to define U
  and V parameters for each point in the **Vertices** input explicitly. If
  checked, then U and V parameters are expected in **SrcU**, **SrcV** inputs.
  Otherwise, the **Vertices** input will expect a list of lists of points for
  each surface, and the node will try to guess U and V coordinates
  automatically. Checked by default.
* **Function**. The specific function used by the node. The available values are:

  * Multi Quadric
  * Inverse
  * Gaussian
  * Cubic
  * Quintic
  * Thin Plate

  The default function is Multi Quadric. `Scipy RBF Functions <https://docs.scipy.org/doc/scipy/reference/generated/scipy.interpolate.Rbf.html>`_

  .. image:: https://github.com/nortikin/sverchok/assets/14288520/1de5c5e8-4dba-455c-b268-8f5d9ac787f9
    :target: https://github.com/nortikin/sverchok/assets/14288520/1de5c5e8-4dba-455c-b268-8f5d9ac787f9

Outputs
-------

This node has the following output:

* **Surface**. The generated Surface object.

Examples of usage
-----------------

Simple example of **XY -> Z** mode usage:

.. image:: https://user-images.githubusercontent.com/284644/87230237-0734d580-c3c8-11ea-90c3-730bb21170c4.png
  :target: https://user-images.githubusercontent.com/284644/87230237-0734d580-c3c8-11ea-90c3-730bb21170c4.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

An example of Matrix input usage; rotated and deformed plane is used as input:

.. image:: https://user-images.githubusercontent.com/284644/87230628-ba9ec980-c3ca-11ea-8551-6fc3e8ab532f.png
  :target: https://user-images.githubusercontent.com/284644/87230628-ba9ec980-c3ca-11ea-8551-6fc3e8ab532f.png

* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Matrix-> :doc:`Matrix Normal </nodes/matrix/matrix_normal>`
* Analyzers-> :doc:`Linear Approximation </nodes/analyzer/linear_approx>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
* Scene-> :doc:`Objects In Lite </nodes/scene/objects_in_lite>`

An example where **UV -> XYZ** mode is required to build a proper surface:

.. image:: https://user-images.githubusercontent.com/284644/87230238-08660280-c3c8-11ea-97d0-87dd31029abe.png
  :target: https://user-images.githubusercontent.com/284644/87230238-08660280-c3c8-11ea-97d0-87dd31029abe.png

* Generator-> :doc:`Cylinder </nodes/generator/cylinder_mk2>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Transform-> :doc:`Randomize </nodes/transforms/randomize>`
* Vector-> :doc:`Vector Polar Output </nodes/vector/vector_polar_out>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`