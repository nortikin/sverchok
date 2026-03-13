Marching Cubes
==============

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4ca44a7b-8df5-4fae-a9a0-bb8a460e5854
  :target: https://github.com/nortikin/sverchok/assets/14288520/4ca44a7b-8df5-4fae-a9a0-bb8a460e5854

Dependencies
------------

This node can optionally use SkImage_ or PyMCubes_ library to work. It can also
work without any dependencies, but slower.

.. _SkImage: https://scikit-image.org/
.. _PyMCubes: https://github.com/pmneila/PyMCubes

Functionality
-------------

This node uses Marching Cubes_ algorithm to find iso-surfaces of given scalar
field, i.e. such surfaces, that for each point on a surface the scalar field
has the given value. Such surfaces are also known as "implicit surfaces".

Surfaces are generated as mesh - vertices and faces.

.. _Cubes: https://en.wikipedia.org/wiki/Marching_cubes

.. image:: https://github.com/nortikin/sverchok/assets/14288520/36b4857e-cc12-4f8a-94e0-aa2e80db5029
  :target: https://github.com/nortikin/sverchok/assets/14288520/36b4857e-cc12-4f8a-94e0-aa2e80db5029

* Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
* Fields-> :doc:`Voronoi Field </nodes/field/voronoi_field>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/baedf54d-2df4-4f43-8fa8-f4d583731c54
  :target: https://github.com/nortikin/sverchok/assets/14288520/baedf54d-2df4-4f43-8fa8-f4d583731c54

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to find the iso-surfaces for. This input is mandatory.
* **Bounds**. Vertices defining the bounds for generated geometry. Only
  bounding box of these points is used. This input is mandatory.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/931c798b-9a73-432b-b85d-9f184ec502c2
      :target: https://github.com/nortikin/sverchok/assets/14288520/931c798b-9a73-432b-b85d-9f184ec502c2

* **Value**. The value of scalar field, for which the iso-surfaces should be
  generated. The default value is 1.0.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/98a222d9-ac36-441a-b7e2-987381dd3585
      :target: https://github.com/nortikin/sverchok/assets/14288520/98a222d9-ac36-441a-b7e2-987381dd3585

    * Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
    * Generator-> :doc:`Box </nodes/generator/box_mk2>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/2f4b814e-e480-4e15-9f0a-8a0b3b637930
      :target: https://github.com/nortikin/sverchok/assets/14288520/2f4b814e-e480-4e15-9f0a-8a0b3b637930

* **SamplesX**, **SamplesY**, **SamplesZ**. Number of scalar field samples to
  be used along X, Y and Z axes. This defines the resolution of surfaces: the
  higher the values, the more precise are the surfaces. Note that computation
  time of this node is proportional to ``SamplesX * SamplesY * SamplesZ``, so
  if you increase each of these values by two times, the computation time will
  increase eight times. The default value is 50. These inputs are available
  only when **Sampling** parameter is set to **Non-uniform**.
* **Samples**. Number of samples of scalar field for X, Y and Z axes. This
  input is used instead of **SamplesX**, **SamplesY** and **SamplesZ** when the
  **Sampling** parameter is set to **Uniform**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/47b1786c-568f-48b1-b0e9-e16c03bfda93
      :target: https://github.com/nortikin/sverchok/assets/14288520/47b1786c-568f-48b1-b0e9-e16c03bfda93
    
    * Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
    * Generator-> :doc:`Box </nodes/generator/box_mk2>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Parameters
----------

This node has the following parameters:

* **Implementation**. This allows to select the algorithm implementation. The following options are possible:

  * SciKit-Image. This is available only if SciKit-Image library is available.
  * PyMCubes. This is available only if PyMCubes library is available.
  * Pure Python. This implementation is slower than other two.

  The default option depends is the first one of available, in this order.

* **Sampling**. The following options are available:

  * **Uniform**. The same number of samples will be used for X, Y and Z axes.
    The number of samples is provided in **Samples** input.
  * **Non-Uniform**. This allows to provide different values for X, Y and Z
    axes, in **SamplesX**, **SamplesY**, **SamplesZ** inputs, correspondingly.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/cf4280dc-8ce2-43fc-85a6-022f28985c17 
      :target: https://github.com/nortikin/sverchok/assets/14288520/cf4280dc-8ce2-43fc-85a6-022f28985c17

  The default option is **Uniform**.

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of generated mesh.
* **Faces**. The faces of generated mesh. Due to the algorithm used, this
  output will always contain only tris.
* **VertexNormals**. Vertex normals. This output is only available if
  **Implementation** parameter is set to **SciKit-Image**.

    .. image:: https://github.com/nortikin/sverchok/assets/14288520/6de95427-b18f-4f68-9775-c9b8fa111dbe
      :target: https://github.com/nortikin/sverchok/assets/14288520/6de95427-b18f-4f68-9775-c9b8fa111dbe

    * Generator-> :doc:`Line </nodes/generator/line_mk4>`
    * Generator-> :doc:`Box </nodes/generator/box_mk2>`
    * Fields-> :doc:`Coordinate Scalar Field </nodes/field/coordinate_scalar_field>`
    * Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Examples of usage
-----------------

This node can be used to generate metaball-like structures:

.. image:: https://user-images.githubusercontent.com/284644/87254841-41bd7180-c49f-11ea-90d8-439b6f0c8dfd.png
  :target: https://user-images.githubusercontent.com/284644/87254841-41bd7180-c49f-11ea-90d8-439b6f0c8dfd.png

* Generator-> :doc:`NGon </nodes/generator/ngon>`
* Fields-> :doc:`Attractor Field </nodes/field/attractor_field_mk2>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Or it is possible to generate mathematically-specified implicit surfaces. The following is known as "Saddle Tower":

.. image:: https://user-images.githubusercontent.com/284644/87254916-c7412180-c49f-11ea-98eb-a271a67df181.png
  :target: https://user-images.githubusercontent.com/284644/87254916-c7412180-c49f-11ea-98eb-a271a67df181.png

* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Spacial-> :doc:`Vector P Field </nodes/spatial/homogenous_vector_field>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`


.. image:: https://github.com/nortikin/sverchok/assets/14288520/49a2e64b-6358-4e3e-811e-a71ed69b568c
  :target: https://github.com/nortikin/sverchok/assets/14288520/49a2e64b-6358-4e3e-811e-a71ed69b568c

* Generator-> :doc:`Box </nodes/generator/box_mk2>`
* Fields-> :doc:`Scalar Field Formula </nodes/field/scalar_field_formula>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Number Range </nodes/number/number_range>`
* Number-> :doc:`Map Range </nodes/number/range_map>`
* Matrix-> :doc:`Matrix In </nodes/matrix/matrix_in_mk4>`
* List->List Main-> :doc:`List Length </nodes/list_main/length>`
* Color-> :doc:`Color In </nodes/color/color_in_mk1>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

.. image:: https://github.com/nortikin/sverchok/assets/14288520/4b774523-e129-490f-918f-b7c3b27f90b9
  :target: https://github.com/nortikin/sverchok/assets/14288520/4b774523-e129-490f-918f-b7c3b27f90b9