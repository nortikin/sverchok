Join Scalar Fields
==================

Functionality
-------------

This node joins (merges) a list of Scalar Field objects by one of supported
mathematical operations, to generate a new Scalar Field.

Inputs
------

This node has the following input:

* **Fields**. The list of scalar fields to be merged.

Parameters
----------

This node has the following parameter:

* **Mode**. This defines the operation used to calculate the new field. The supported operations are:

  * **Minimum**. Take the minimal value of all fields: MIN(S1(X), S2(X), ...).
  * **Maximum**. Take the maximum value of all fields: MAX(S1(X), S2(X), ...)
  * **Average**. Take the average (mean) value of all fields: (S1(X) + S2(X) + ...) / N.
  * **Sum**. Take the sum of all fields: S1(X) + S2(X) + ...
  * **Voronoi**. Take the difference between two smallest field values: ABS(S1(X) - S2(X)).

Outputs
-------

This node has the following output:

* **Field**. The generated scalar field.

Examples of usage
-----------------

Take the minimum of several attraction fields:

.. image:: https://user-images.githubusercontent.com/284644/79610315-bdfb1f80-8111-11ea-886d-030538a50e5d.png

The same with Voronoi mode:

.. image:: https://user-images.githubusercontent.com/284644/79610367-d834fd80-8111-11ea-9d3b-95b671256904.png

