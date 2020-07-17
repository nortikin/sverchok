Marching Cubes
==============

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

Inputs
------

This node has the following inputs:

* **Field**. Scalar field to find the iso-surfaces for. This input is mandatory.
* **Bounds**. Vertices defining the bounds for generated geometry. Only
  bounding box of these points is used. This input is mandatory.
* **Value**. The value of scalar field, for which the iso-surfaces should be
  generated. The default value is 1.0.
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

  The default option is **Uniform**.

Outputs
-------

This node has the following outputs:

* **Vertices**. The vertices of generated mesh.
* **Faces**. The faces of generated mesh. Due to the algorithm used, this
  output will always contain only tris.
* **VertexNormals**. Vertex normals. This output is only available if
  **Implementation** parameter is set to **SciKit-Image**.

Examples of usage
-----------------

This node can be used to generate metaball-like structures:

.. image:: https://user-images.githubusercontent.com/284644/87254841-41bd7180-c49f-11ea-90d8-439b6f0c8dfd.png

Or it is possible to generate mathematically-specified implicit surfaces. The following is known as "Saddle Tower":

.. image:: https://user-images.githubusercontent.com/284644/87254916-c7412180-c49f-11ea-98eb-a271a67df181.png

