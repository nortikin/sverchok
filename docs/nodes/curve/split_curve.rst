Split Curve
===========

Functionality
-------------

This node splits one Curve object into several Curves, by dividing it at some
values of curve's T parameter. The values of T parameter, at which the split
should be made, can be either specified manually or calculated automatically by
the provided number of cuts.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be split. This input is mandatory.
* **Segments**. Number of pieces the curve is to be split into. This input is
  available only if **Mode** parameter is set to **Even**. The default value is
  10.
* **Split**. The value of curve's T parameter, at which the curve is to be
  split. This input is only available when **Mode** parameter is set to
  **Explicit**. This input can consume several values per each curve. The
  default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Mode**. This defines how the values of curve's T parameter, at which the
  curve is to be split, are determined. The available options are:

  * **Even**. The curve will be split by even ranges of T parameter. Number of
    pieces to split into is defined in the **Segments** input. For example, if
    curve domain is ``[0; 1]``, and **Segments** input is set to ``2``, then
    the curve will be split into two segments with domains of ``[0; 0.5]`` and
    ``[0.5; 1]``.
  * **Explicit**. The values of T parameter are provided in the **Split** input.

* **Recale to 0..1**. If checked, then parametrizations of generated Curve
  objects will be adjusted, so that each of them will have domain of ``[0;
  1]``. Otherwise, the domain of generated Curve objects will be equal to
  corresponding part of initial curve's domain. Unchecked by default.
* **Join**. If checked, then the node will generate single list of pieces for
  each provided list of Curve objects. Otherwise, the node will generate
  separate list of pieces for each provided Curve object. Unchecked by default.

Outputs
-------

This node has the following output:

* **Curves**. The generated Curve objects.
