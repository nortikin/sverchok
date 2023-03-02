Solid Section
=============

.. image:: https://user-images.githubusercontent.com/66558924/212058287-c0426edb-7f56-425d-8e7c-cc99ff8700c7.jpg

Dependencies
------------

This node requires `FreeCAD library <https://nortikin.github.io/sverchok/docs/data_structure/solids.html>`_ to work.


Functionality
-------------

This node generates the intersection Curves and Points between different Shapes including Solids, Solid Faces, Solid Edges, NURBS Surfaces and NURBS Curves.

The node can operate on pair of objects ("Shape A" intersects "Shape B") or on pair of lists of objects.

Inputs
------

This node has the following inputs:

* **Shape A**. The first object to perform operation on. This input is
  mandatory and can accept a list of Shapes*.
* **Shape B**. The second object to perform operation on. This input is
  mandatory and can accept a list of Shapes*.
  
  Curves (NURBS Curves and Solid Edges) cannot be mixed with other Shape types.  
  For example [<NURBS_Curve>, <Solid_Edge>, <Solid>] is not a valid input list.
  
  Valid inputs are [<NURBS_Curve1>, <NURBS_Curve2>, <Solid_Edge>] or [<NURBS_Curve>, <Solid_Edge>]  
  or [<NURBS_Surface1>, <Solid>, <NURBS_Surface2>] etc.

Options
-------

This node has the following parameters:

* **NURBS Output**. This parameter is available in the N panel only. If
  checked, the node will generate curves in NURBS representation. Otherwise, it
  will generate standard FreeCAD curves (Solid Edge curves). Unchecked by default.
  
Outputs
-------

This node has the following outputs:

* **Vertices**. The resulting intersection (puncture) Points or endpoints of the intersection Curves.  
* **Curves**. The resulting intersection Curves.

Product variations of the Section operation:

* Solid × Curve → Point (common case) or Curve (if the curve or part of the curve overlays with the solid)

* Solid × Surface → Curve (common case) or Point (when both are only touching)

* Curve × Surface → Point (common case) or Curve (if the curve or part of the curve overlays with the surface)

* Solid × Solid → Curve (common case) or Point (when both are only touching)

* Surface × Surface → Curve (common case) or Point (when both are only touching)

* Curve × Curve → Point (common case) or Curve (if curves overlay at a certain segment)


If no intersections are found the node will output empty lists.


Examples
--------

**Curve** × **Curve** → **Points**:

.. image:: https://user-images.githubusercontent.com/66558924/212648237-1f4f052f-1a61-496c-a0db-27eebb8c9524.jpg



**Curves** × **Surface** → **Points and Curve**:

.. image:: https://user-images.githubusercontent.com/66558924/212650377-26c0af14-1b6d-4039-b655-7719ae4dee03.jpg


**Surface** × **List of Surfaces** → **Curves**:

.. image:: https://user-images.githubusercontent.com/66558924/212664158-65bc2f04-0376-4b8a-bbbf-05812fc4e76e.jpg


**Surface** × **Solid** → **Curves**:

.. image:: https://user-images.githubusercontent.com/66558924/212653198-d616f3ad-d533-4409-a2bf-2e65213f6939.jpg


