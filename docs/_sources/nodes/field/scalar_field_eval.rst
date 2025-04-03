Evaluate Scalar Field
=====================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3432d895-ff38-4572-a457-2042af551134
  :target: https://github.com/nortikin/sverchok/assets/14288520/3432d895-ff38-4572-a457-2042af551134

Functionality
-------------

This node calculates the value of the provided Scalar Field at the specified point.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/714094c1-ba64-4de9-84e6-b9287ead8b51
  :target: https://github.com/nortikin/sverchok/assets/14288520/714094c1-ba64-4de9-84e6-b9287ead8b51

Inputs
------

This node has the following inputs:

* **Field**. The field to be evaluated. This input is mandatory.
* **Vertices**. The points at which the field is to be evaluated. The default value is `(0, 0, 0)`.

Parameters
----------

* **Output NumPy**. Outputs NumPy arrays in stead of regular python lists. Improves performance

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/ea333341-963f-4c80-8ea3-354d836c2d93
      :target: https://github.com/nortikin/sverchok/assets/14288520/ea333341-963f-4c80-8ea3-354d836c2d93

Outputs
-------

This node has the following output:

* **Value**. The values of the field at the specified points.

Performance Notes
-----------------

This node works faster when the vertices list are NumPy arrays

Example of usage
----------------

Example of Description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/8362e1b2-a630-4538-9fc8-370d4b9ae22e
  :target: https://github.com/nortikin/sverchok/assets/14288520/8362e1b2-a630-4538-9fc8-370d4b9ae22e

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/760c547b-c6b8-4405-b755-a3af63511783
  :target: https://github.com/nortikin/sverchok/assets/14288520/760c547b-c6b8-4405-b755-a3af63511783

---------

Use the values of scalar field to scale the cubes:

.. image:: https://user-images.githubusercontent.com/284644/79475246-dc352280-8020-11ea-8f8d-ddd3d6ca7a73.png
  :target: https://user-images.githubusercontent.com/284644/79475246-dc352280-8020-11ea-8f8d-ddd3d6ca7a73.png

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`