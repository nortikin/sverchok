Intersect NURBS Curves
======================

Dependencies
------------

This node requires either SciPy_ library, or FreeCAD_ libraries to work.

.. _SciPy: https://scipy.org/
.. _FreeCAD: https://www.freecadweb.org/

Functionality
-------------

This node tries to find all intersections of provided Curve objects. This node
can work only with NURBS or NURBS-like curves.

Inputs
------

This node has the following inputs:

* **Curve1**. The first curve. This input is mandatory.
* **Curve2**. The second curve. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Implementation**. Implementation of numeric algorithm to be used. The
  available options are:

  * **FreeCAD**. Use implementation from FreeCAD_ library. This option is
    available when FreeCAD library is installed.
  * **SciPy**. Use implementation based on SciPy_ library. This option is
    available when SciPy library is installed.

  In general, FreeCAD implementation is considered to be faster, more precise,
  and better tested. However, it does not allow one to control intersection
  tolerances, while SciPy implementation does.

  By default, the first available implementation is used.

* **Matching**. This defines how lists of input curves are matched. The
  available options are:

  * **Longest**. The node will use input lists in parallel: first curve from
    the first list with first curve from the second list, then second curve
    from first list with second curve from the second list, and so on. In case
    two lists have different lengths, in the shortest one, the last curve will
    be repeated as many times as required to match lengths.

  * **Cross**. The node will use input lists in "each-to-each" mode: first
    curve from first list with each curve from the second list, then second
    curve from first list with each curve from the second list, and so on.

  The default option is **Longest**.

* **Find single intersection**. If checked, the node will search only one
  intersection for each pair of input curves. Otherwise, it will search for all
  intersections. Checked by default.
* **Curves do intersect**. If checked, then the node will fail if two curves do
  not intersect. Otherwise, it will just output empty list of intersections.
  Unchecked by default.
* **Split by row**. This parameter is available only when **Matching**
  parameter is set to **Cross**. If checked, the node will output a separate
  list of intersections for each curve from the first list. Otherwise, the node
  will output a single flat list with all intersections of each curve with
  each. Checked by default.
* **Precision**. This parameter is available in the N panel only, and only when
  **Implementation** parameter is set to **SciPy**. This defines the allowed
  tolerance of numeric method - the maximum allowed distance between curves,
  which is considered as intersection. The default value is 0.001.
* **Numeric method**. This parameter is available in the N panel only, and only when
  **Implementation** parameter is set to **SciPy**. This defines numeric method
  to be used. The available options are: Nelder-Mead, L-BFGS-B, SLSQP, Powell,
  Trust-Cosntr.

Outputs
-------

This node has the following output:

* **Intersections**. The list of intersection points.

Example of Usage
----------------

Find three intersections of two curves:

.. image:: https://user-images.githubusercontent.com/284644/123548323-c3281580-d77d-11eb-83fb-8216aad82d0f.png

Find twelve intersections of two series of curves:

.. image:: https://user-images.githubusercontent.com/284644/123548414-24e87f80-d77e-11eb-86aa-348b6c7c0322.png

