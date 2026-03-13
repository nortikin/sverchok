Generate Knotvector
===================

Functionality
-------------

This node provides several ways of generating a knotvector for building (or
interpolation) of NURBS curves and surfaces.

Inputs
------

This node has the following inputs:

* **Vertices**. Points to be used to calculate distance between them and
  calculate knotvector based on those distances. This input is available and
  mandatory only when **Mode** parameter is set to **From Points**.
* **Knots**. Values of T parameter, which will be used to calculate knotvector.
  This input is available and mandatory only when **Mode** parameter is set to
  **From T values**.
* **Degree**. Degree of the curve (or surface), for which the knotvector is to
  be generated. The default value is 3.
* **ControlPointsCount**. Number of curve (or surface) control points. This
  input is available either when **Mode** parameter is set to **Uniform**, or
  when **Set control points number** is checked. The default value is 4.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the knotvector will be generated. The available options are:

  * **Uniform**. Generate a uniform knotvector. Such knotvector is defined by
    number of control points and degree. The knotvector can be generated as
    clamped or non-clamped, depending on **Clamped** parameter.
  * **From Points**. Calculate distances between some points, and generate a
    non-uniform knotvector based on those distances. This option can be useful
    for some custom interpolation algorithms. The generated knotvector will be
    always clamped.
  * **From T Values**. Generate a knotvector based on T values, which
    correspond to some points. This can be useful for some custom interpolation
    algorithms, if no standard metric fits you. The generated knotvector will
    be always clamped.

* **Metric**. The metric to be used to calculate distances between points. This
  parameter is only available when **Mode** parameter is set to **From
  Points**. The default option is **Euclidean**.
* **Set control points number**. This parameter is only available when **Mode**
  parameter is set to **From Points** or **From T Values**. If checked, the
  node will allow to specify arbitrary number of curve's (or surface's) control
  points, even though usually it should be derived from the number of points or
  T values provided. Unchecked by default.
* **Include endpoints**. This parameter is only available when **Mode**
  parameter is set to **From Points** or **From T Values**. If checked, the
  algorithm of knotvector generation will be changed in such a way, that first
  and last T values (or points positions) will also affect knot values, in the
  beginning and in the end of knotvector, respectively. With usual algorithm,
  they do not. When this parameter is checked, the number of control points
  used to generate the knotvector will be actually increased by 2. This can be
  useful for some custom interpolation algorithms, when you need to add another
  degree of freedom near curve ends - for example, to be able to specify custom
  curve tangents. Unchecked by default.
* **Clamped**. This parameter is available only when **Mode** parameter is set
  to **Uniform**. This defines whether the node will generated a clamped
  knotvector or non-clamped. Checked by default.
* **Numpy output**. This parameter is available in the N panel only. If
  checked, the node will output numbers as NumPy arrays. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **Knotvector**. Generated knotvector.
* **Knots**. Knot values - all unique values from the knotvector.

