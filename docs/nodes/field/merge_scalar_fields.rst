Join Scalar Fields
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/88f88ac5-2e29-4fa5-9a4b-21fc6e4a1695
  :target: https://github.com/nortikin/sverchok/assets/14288520/88f88ac5-2e29-4fa5-9a4b-21fc6e4a1695

Functionality
-------------

This node joins (merges) a list of Scalar Field objects by one of supported
mathematical operations, to generate a new Scalar Field.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/eba7af06-e8e7-41d0-83d6-6e6c5aaf912a
  :target: https://github.com/nortikin/sverchok/assets/14288520/eba7af06-e8e7-41d0-83d6-6e6c5aaf912a

.. image:: https://github.com/nortikin/sverchok/assets/14288520/5de66c30-c2b0-4d27-a8b2-f402d8861469
  :target: https://github.com/nortikin/sverchok/assets/14288520/5de66c30-c2b0-4d27-a8b2-f402d8861469

* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`


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

      .. image:: https://github.com/nortikin/sverchok/assets/14288520/f744a4c3-7794-43ca-bb7e-f6b344f7c0fa
        :target: https://github.com/nortikin/sverchok/assets/14288520/f744a4c3-7794-43ca-bb7e-f6b344f7c0fa

Outputs
-------

This node has the following output:

* **Field**. The generated scalar field.

Examples of usage
-----------------

*Example of descriptions*:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/81b3c49e-f664-42f7-9909-50736ded6a37
  :target: https://github.com/nortikin/sverchok/assets/14288520/81b3c49e-f664-42f7-9909-50736ded6a37

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Marching Cubes </nodes/surface/marching_cubes>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* List->List Main-> :doc:`List Join </nodes/list_main/join>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Take the minimum of several attraction fields:

.. image:: https://user-images.githubusercontent.com/284644/79610315-bdfb1f80-8111-11ea-886d-030538a50e5d.png
  :target: https://user-images.githubusercontent.com/284644/79610315-bdfb1f80-8111-11ea-886d-030538a50e5d.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Distance From a Point </nodes/field/scalar_field_point>`
* Fields-> :doc:`Scalar Field Math </nodes/field/scalar_field_math>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

The same with Voronoi mode:

.. image:: https://user-images.githubusercontent.com/284644/79610367-d834fd80-8111-11ea-9d3b-95b671256904.png
  :target: https://user-images.githubusercontent.com/284644/79610367-d834fd80-8111-11ea-9d3b-95b671256904.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Distance From a Point </nodes/field/scalar_field_point>`
* Fields-> :doc:`Scalar Field Math </nodes/field/scalar_field_math>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`