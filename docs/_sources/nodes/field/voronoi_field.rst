Voronoi Field
=============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/56080a36-f2d3-4d82-b4b2-d9f9de66c2f2
  :target: https://github.com/nortikin/sverchok/assets/14288520/56080a36-f2d3-4d82-b4b2-d9f9de66c2f2

Functionality
-------------

This node generates a Vector Field and a Scalar Field, which are defined
according to the Voronoi diagram for the specified set of points ("voronoi
sites"):

* The scalar field value for some point is calculated as the difference between
  distances from this point to two nearest Voronoi sites;
* The vector field vector for some point points from this point towards the
  nearest Voronoi site. The absolute value of this vector is equal to the value
  of Voronoi scalar field in this point.

So, the set of points (planar areas), where scalar field equals to zero, is
exactly the Voronoi diagram for the specified set of sites.

.. image:: https://github.com/nortikin/sverchok/assets/14288520/d9ca632e-4d5c-4b9f-94c3-970fb2bbeea9
  :target: https://github.com/nortikin/sverchok/assets/14288520/d9ca632e-4d5c-4b9f-94c3-970fb2bbeea9

* Generator-> :doc:`NGon </nodes/generator/ngon>`

Inputs
------

This node has the following input:

* **Vertices**. The set of points (sites) to form Voronoi field for. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Metric**. The metric to be used for creating Voronoi field. The available options are:

  * **Euclidean**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/0426ac78-410d-4618-8be0-e511be560dbb
      :target: https://github.com/nortikin/sverchok/assets/14288520/0426ac78-410d-4618-8be0-e511be560dbb

  * **Manhattan**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/c3e83ab6-12bc-4757-baa0-c1ba260e5b98
      :target: https://github.com/nortikin/sverchok/assets/14288520/c3e83ab6-12bc-4757-baa0-c1ba260e5b98

  * **Chebyshev**

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/20b972a2-f1da-4db8-8212-3552b7673b48
      :target: https://github.com/nortikin/sverchok/assets/14288520/20b972a2-f1da-4db8-8212-3552b7673b48

  * **Custom**. A generic Minkowski metric defined by formula
    ``sum(abs(dx_i)**P)**(1.0/P)``, where P is defined in the Exponent
    parameter.
   
    .. image:: https://github.com/nortikin/sverchok/assets/14288520/aaea43d7-e351-414c-815d-43f7cc81a19a
      :target: https://github.com/nortikin/sverchok/assets/14288520/aaea43d7-e351-414c-815d-43f7cc81a19a

  The default value is **Euclidean**.

* **Exponent**. This parameter is available only when **Metric** parameter is
  set to **Custom**. Exponent for generic Minkowski distance. The available
  values are from 1.0 to infinity. The default value is 2.0, which defines
  Euclidean metric.

Outputs
-------

This node has the following outputs:

* **SField**. Voronoi scalar field.
* **VField**. Voronoi vector field.

Examples of usage
-----------------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/ea913a4c-ffcb-434a-85ab-9aba442b1d2b
  :target: https://github.com/nortikin/sverchok/assets/14288520/ea913a4c-ffcb-434a-85ab-9aba442b1d2b

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Surfaces-> :doc:`Evaluate Surface </nodes/surface/evaluate_surface>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

.. image:: https://github.com/nortikin/sverchok/assets/14288520/1fde6ce3-ff62-4d22-a58e-2bb5ccb3715b
  :target: https://github.com/nortikin/sverchok/assets/14288520/1fde6ce3-ff62-4d22-a58e-2bb5ccb3715b

* Generator-> :doc:`Line </nodes/generator/line_mk4>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Fields-> :doc:`Evaluate Vector Field </nodes/field/vector_field_eval>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Transform-> :doc:`Noise Displace </nodes/transforms/noise_displace>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* Color-> :doc:`Color Input </nodes/color/color_input>`
* Color-> :doc:`Color Out </nodes/color/color_out_mk1>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/279736be-903a-45c7-aba4-0fdd6bbf09b7
  :target: https://github.com/nortikin/sverchok/assets/14288520/279736be-903a-45c7-aba4-0fdd6bbf09b7

---------

Use Voronoi scalar field of three points (marked with red spheres) to scale blue spheres:

.. image:: https://user-images.githubusercontent.com/284644/79604012-cf8afa00-8106-11ea-9283-0856cd0a0a6c.png
  :target: https://user-images.githubusercontent.com/284644/79604012-cf8afa00-8106-11ea-9283-0856cd0a0a6c.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Fields-> :doc:`Scalar Field Math </nodes/field/scalar_field_math>`
* Fields-> :doc:`Evaluate Scalar Field </nodes/field/scalar_field_eval>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Visualize the lines of corresponding vector field:

.. image:: https://user-images.githubusercontent.com/284644/79604015-d0bc2700-8106-11ea-9f5d-621fdc900fcb.png
  :target: https://user-images.githubusercontent.com/284644/79604015-d0bc2700-8106-11ea-9f5d-621fdc900fcb.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Vector Field Lines </nodes/field/vector_field_lines>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Number-> :doc:`A Number </nodes/number/numbers>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

---------

Apply the vector field to some box:

.. image:: https://user-images.githubusercontent.com/284644/79604016-d0bc2700-8106-11ea-8863-dbb9af6ab8b3.png
  :target: https://user-images.githubusercontent.com/284644/79604016-d0bc2700-8106-11ea-8863-dbb9af6ab8b3.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Fields-> :doc:`Apply Vector Field </nodes/field/vector_field_apply>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`
