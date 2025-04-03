Vectors Attraction
==================

.. image:: https://user-images.githubusercontent.com/14288520/189442071-9b5734dc-8702-4bfb-8b0c-d1d63531b502.png
  :target: https://user-images.githubusercontent.com/14288520/189442071-9b5734dc-8702-4bfb-8b0c-d1d63531b502.png

Functionality
-------------

This node calculates vectors directed from input vertices to specified
attractor. Vector lengths are calculated by one of physics-like falloff laws
(like 1/R^2), so it looks like attractor attracts vertices, similar to gravity
force, for example.
Output vectors can be used to move vertices along them, for example.

Inputs
------

This node has the following inputs:

- **Vertices**
- **Center**. Center of used attractor. Exact meaning depends on selected attractor type.
- **Direction**. Direction of used attractor. Exact meaning depends on selected
  attractor type. Not available if attractor type is **Point**.
- **Amplitude**. Coefficient of attractor power. Zero means that all output
  vectors will be zero. If many values are provided, each value will be matched
  to one vertex.
- **Coefficient**. Scale coefficient for falloff law. Exact meaning depends on
  selected falloff type. Available only for falloff types **Inverse exponent**
  and **Gauss**. If many values are provided, each value will be matched to one
  vertex.

Parameters
----------

This node has the following parameters:

- **Attractor type**. Selects form of used attractor. Available values are:

  - **Point**. Default value. In simple case, attractor is just one point
    specified in **Center** input. Several points can be passed in that input;
    the method of attraction vector calculation in this case is controlled by
    the **Points mode** parameter.
  - **Line**. Attractor is a straight line, defined by a point belonging to
    this line (**Center** input) and directing vector (**Direction** input).
  - **Plane**. Attractor is a plane, defined by a point belonging to this line
    (**Center** input) and normal vector (**Direction** input).

.. image:: https://user-images.githubusercontent.com/14288520/200179955-7dfe5db7-5c36-4d3a-b27e-f42f89b6850a.png
  :target: https://user-images.githubusercontent.com/14288520/200179955-7dfe5db7-5c36-4d3a-b27e-f42f89b6850a.png

- **Points mode**. This defines how attraction vectors are calculated in case
  several points are provided as attraction centers. The available modes are:

  - **Average**. Attracting force for each vertex will be calculated as
    average of attracting forces towards each attractor point.
  - **Nearest**. Attracting force for each vertex will be calculated as the attracting force towards the nearest of attractor points.

   The default mode is **Average** (which is more physically correct). This
   parameter is available only if **Attractor type** parameter is set to
   **Point**.

.. image:: https://user-images.githubusercontent.com/14288520/200180797-4ac81fe7-6a59-445a-837e-5b5ac8181541.png
  :target: https://user-images.githubusercontent.com/14288520/200180797-4ac81fe7-6a59-445a-837e-5b5ac8181541.png

- **Falloff type**. Used falloff law. Available values are:

  - **Inverse**. Falloff law is 1/R, where R is distance from vertex to attractor.
  - **Inverse square**. Falloff law is 1/R^2. This law is most common in physics (gravity and electromagnetizm), so this is the default value.
  - **Inverse cubic**. Falloff law is 1/R^3.
  - **Inverse exponent**. Falloff law is `exp(- C * R)`, where R is distance from vertex to attractor, and C is value from **Coefficient** input.
  - **Gauss**. Falloff law is `exp(- C * R^2 / 2)`, where R is distance fromcvertex to attractor, and C is value from **Coefficient** input.

.. image:: https://user-images.githubusercontent.com/14288520/205487361-bde8ef53-a23a-43dd-9d48-01892b1d3c75.png
  :target: https://user-images.githubusercontent.com/14288520/205487361-bde8ef53-a23a-43dd-9d48-01892b1d3c75.png

- **Clamp**. Whether to restrict output vector length with distance from vertex
  to attractor. If not checked, then attraction vector length can be very big
  for vertices close to attractor, depending on selected falloff type. Default
  value is True.

.. image:: https://user-images.githubusercontent.com/14288520/200178995-517be50c-12bb-4e28-8188-66d608dba774.png
  :target: https://user-images.githubusercontent.com/14288520/200178995-517be50c-12bb-4e28-8188-66d608dba774.png

.. image:: https://user-images.githubusercontent.com/14288520/200178869-bb8de78b-861f-4073-8e1d-13f56e8c6561.png
  :target: https://user-images.githubusercontent.com/14288520/200178869-bb8de78b-861f-4073-8e1d-13f56e8c6561.png

Outputs
-------

This node has the following outputs:

- **Vectors**. Calculated attraction force vectors. 
- **Directions**. Unit vectors in the same directions as attracting force.
- **Coeffs**. Lengths of calculated attraction force vectors.

See also
--------

* Analyzers-> :doc:`Proportional Edit Falloff </nodes/analyzer/proportional>`

Examples of usage
-----------------

Most obvious case, just a plane attracted by single point:

.. image:: https://user-images.githubusercontent.com/14288520/189442196-a246ba9d-1852-4b88-93ac-d01748d698a6.png
  :target: https://user-images.githubusercontent.com/14288520/189442196-a246ba9d-1852-4b88-93ac-d01748d698a6.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Plane attracted by single point, with Clamp unchecked:

.. image:: https://user-images.githubusercontent.com/14288520/189442237-8847f013-e8db-4f07-baba-7ca61cc48a54.png
  :target: https://user-images.githubusercontent.com/14288520/189442237-8847f013-e8db-4f07-baba-7ca61cc48a54.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Not so obvious, plane attracted by circle (red points):

.. image:: https://user-images.githubusercontent.com/14288520/189442273-3dd6fc22-3aaa-45f9-bbad-a0cf277ce5b2.png
  :target: https://user-images.githubusercontent.com/14288520/189442273-3dd6fc22-3aaa-45f9-bbad-a0cf277ce5b2.png

* Generator-> :doc:`Circle </nodes/generator/circle>`
* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Coefficients can be used without directions:

.. image:: https://user-images.githubusercontent.com/14288520/189442305-c6a53789-56be-4927-bdda-7671ac23df0a.png
  :target: https://user-images.githubusercontent.com/14288520/189442305-c6a53789-56be-4927-bdda-7671ac23df0a.png

* Generator-> :doc:`Plane </nodes/generator/plane_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Analyzers-> :doc:`Component Analyzer </nodes/analyzer/component_analyzer>`
* Modifiers->Modifier Change-> :doc:`Extrude Separate Faces </nodes/modifier_change/extrude_separate>`

Torus attracted by a line along X axis:

.. image:: https://user-images.githubusercontent.com/14288520/189442343-9454a24b-796f-4cb7-ade8-82f61bcc16bc.png
  :target: https://user-images.githubusercontent.com/14288520/189442343-9454a24b-796f-4cb7-ade8-82f61bcc16bc.png

* Generator-> :doc:`Torus </nodes/generator/torus_mk2>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`

Sphere attracted by a plane:

.. image:: https://user-images.githubusercontent.com/14288520/189442379-e73afdc2-54c5-4721-90bc-9e69a0470fb9.png
  :target: https://user-images.githubusercontent.com/14288520/189442379-e73afdc2-54c5-4721-90bc-9e69a0470fb9.png

* Generator-> :doc:`IcoSphere </nodes/generator/icosphere>`
* Transform-> :doc:`Move </nodes/transforms/move_mk3>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer Draw </nodes/viz/viewer_draw_mk4>`