Vector Field Lines
==================

.. image:: https://github.com/nortikin/sverchok/assets/14288520/2864ff02-7bb6-48a3-9c47-c1e4fdab3e7d
  :target: https://github.com/nortikin/sverchok/assets/14288520/2864ff02-7bb6-48a3-9c47-c1e4fdab3e7d

Functionality
-------------

This node visualizes a Vector Field object by generating lines of that field. More precisely, given the point X and field VF, the node does the following:

* takes original point X
* Applies the field to it with small coefficient, to create a point X1 = X + K * VF(X)
* Applies the field to X1 with small coefficient, to create a point X2 = X1 + K * VF(X1)
* And so on, repeating some number of times.

And then the edges are created between these points. When the coefficient is
small enough, and the number of iterations is big enough, such lines represent
trajectories of material points, when they are moved by some force field.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a765eed2-b18e-42e7-9d34-1d0249ad17ba
  :target: https://github.com/nortikin/sverchok/assets/14288520/a765eed2-b18e-42e7-9d34-1d0249ad17ba

.. image:: https://github.com/nortikin/sverchok/assets/14288520/3a7dce66-207c-4008-b898-882552837ac4
  :target: https://github.com/nortikin/sverchok/assets/14288520/3a7dce66-207c-4008-b898-882552837ac4

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be visualized. This input is mandatory.
* **Vertices**. The points at which to start drawing vector field lines. This input is mandatory.
* **Step**. Vector field application coefficient. If **Normalize** parameter is
  checked, then this coefficient is divided by vector norm. The default value
  is 0.1.
* **Iterations**. The number of iterations. The default value is 10.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/a42be49c-1075-4094-a247-f4efd71c8cf9
      :target: https://github.com/nortikin/sverchok/assets/14288520/a42be49c-1075-4094-a247-f4efd71c8cf9

Parameters
----------

This node has the following parameters:

* **Normalize**. If checked, then all edges of the generated lines will have
  the same length (defined by **Steps** input). Otherwise, length of segments
  will be proportional to vector norms. Checked by default.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/f99381d2-603d-4da5-98cd-daf99a4d938a
      :target: https://github.com/nortikin/sverchok/assets/14288520/f99381d2-603d-4da5-98cd-daf99a4d938a

* **Join**. If checked, join all lines into single mesh object. Checked by default.
* **Output NumPy**. Outputs NumPy arrays in stead of regular python lists. Improves performance

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/e840093e-036d-4864-9f28-a30d0fe6754e
      :target: https://github.com/nortikin/sverchok/assets/14288520/e840093e-036d-4864-9f28-a30d0fe6754e


Outputs
-------

* **Vertices**. The vertices of generated lines.
* **Edges**. The edges of generated lines.

Performance Notes
-----------------

This node works faster when the vertices list are NumPy Arrays

Example of usage
----------------

Example of description:

.. image:: https://github.com/nortikin/sverchok/assets/14288520/a05a6685-e422-4cf6-b2f2-d7ef458eb649
  :target: https://github.com/nortikin/sverchok/assets/14288520/a05a6685-e422-4cf6-b2f2-d7ef458eb649

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Number-> :doc:`List Input </nodes/number/list_input>`
* Fields-> :doc:`RBF Vector Field </nodes/field/minimal_vfield>`
* ADD: Number-> :doc:`Scalar Math </nodes/number/scalar_mk4>`
* Vector-> :doc:`Vector Out </nodes/vector/vector_out>`
* Vector-> :doc:`Vector Polar Input </nodes/vector/vector_polar_in>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/52ece8f1-58c7-4deb-b119-9cabb7af6d15
  :target: https://github.com/nortikin/sverchok/assets/14288520/52ece8f1-58c7-4deb-b119-9cabb7af6d15

---------

Visualize some vector field:

.. image:: https://user-images.githubusercontent.com/284644/79495842-a56e0500-803e-11ea-91ed-611abf181ec2.png
  :target: https://user-images.githubusercontent.com/284644/79495842-a56e0500-803e-11ea-91ed-611abf181ec2.png

* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Fields-> :doc:`Vector Field Math </nodes/field/vector_field_math>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`