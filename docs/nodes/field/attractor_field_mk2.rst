Attractor Field
===============

Functionality
-------------

This node generates a Vector Field and a Scalar Field, which are calculated as
force attracting points towards some objects. Several types of attractor
objects are supported. Several physics-like falloff laws are supported.
Falloffs similar to standard proportional editing mode are supported too (they
are marked with `(P)` in the name).

The scalar field generated equals to the norm of the vector field - i.e., the amplitude of the attracting force.

Inputs
------

This node has the following inputs:

* **Center**. The exact meaning of this input depends on the **Attractor type** parameter:

  * If attractor type is **Point**, then this is the attracting point itself;
  * if attractor type is **Line**, then this is the point lying on the attracting line;
  * if attractor type is **Plane**, then this is the point lying on the attracting plane.
  * if attractor type is **Mesh - Faces** or **Mesh - Faces**, then this is the set of mesh vertices.
  * If attractor type is **Circle**, then this is the center of the circle.

  It is possible to provide several attracting points. The default value is `(0, 0, 0)` (origin).

* **Direction**. The exact meaning of this input depends on the **Attractor type** parameter:

  * if attractor type is **Line**, then this is the directing vector of the line;
  * if attractor type is **Plane**, then this is the normal vector of the plane.
  * with other attractor types, this input is not available.

  The default value is `(0, 0, 1)` (Z axis).

* **Edges**. The edges of the attracting mesh. This input is available only
  when **Attractor type** parameter is set to **Mesh - Edges**.
* **Faces**. The faces of the attracting mesh. This input is available only
  when **Attractor type** parameter is set to **Mesh - Faces**.
* **Radius**. Circle radius. This input is only available when **Attractor type** parameter is set to **Circle**.
* **Amplitude**. The attracting force amplitude. The default value is 0.5.
* **Coefficient**. The coefficient used in the attracting force falloff
  calculation formula. The exact meaning of this input depends on fallof type:
  
   * If **Falloff type** is set to **Inverse exponent** or **Gauss**, then this
     is the coefficient K in the corresponding formula: ``exp(-K*R)`` or
     ``exp(-K*x^2/2)``.
   * If **Falloff type** is set to one of proportional editing modes (one
     starting with ``(P)`` prefix), this is the radius of proportional editing
     falloff.
   * For other falloff types, this input is not available.
     
   The default value is 0.5.

Parameters
----------

This node has the following parameters:

* **Attractor type**. The type of attractor object being used. The available values are:

   * **Point** is defined in the corresponding input.
   * **Line** is defined by a point and the directing vector.
   * **Plane** is defined by a point and the normal vector.
   * **Mesh - Faces** is defined by vertices and faces.
   * **Mesh - Edges** is defined by vertices and edges.

   The default value is **Point**.

* **Join mode**. This determines how the distance is calculated when multiple
  attraction centers are provided. The available values are:

  * **Average**. Calculate the average of the attracting forces towards the
    provided centers. This mode is used in physics. This option is the default
    one.
  * **Nearest**. Use only the force of the attraction towards the nearest attraction center.
  * **Separate**. Generate a separate field of attraction force for each attraction center.

* **Signed**. This parameter is available only when **Attractor type**
  parameter is set to **Mesh - faces**. If checked, then the resulting scalar field
  will be signed: it will have positive values at the one side of the mesh
  (into which the mesh normals are pointing), and negative values at the other
  side of the mesh. Otherwise, the scalar field will have positive values
  everywhere. This flag does not affect the calculated vector field. Unchecked
  by default.
* **Falloff type**. The force falloff type to be used. The available values are:

   * **None - R**. Do not use falloff: the force amplitude is proportional to the distance from the attractor object (grows with the distance).
   * **Inverse - 1/R**. Calculate the force value as 1/R.
   * **Inverse square - 1/R^2**. Calculate the force value as `1/R^2`. This law is most commonly used in physics.
   * **Inverse cubic - 1/R^3**. Calculate the force value as `1/R^3`.
   * **Inverse exponent - Exp(-R)**. Calculate the force value as `Exp(- K*R)`.
   * **Gauss - Exp(-R^2/2)**. Calculate the force value as `Exp(- K * R^2/2)`.
   * **(P) Smooth**. Equivalent of "Smooth" proportional editing falloff.
   * **(P) Sphere**. Equivalent of "Sphere" proportional editing falloff.
   * **(P) Root**. Equivalent of "Root" proportional editing falloff.
   * **(P) Inverse Square**. Equivalent of "Inverse Square" proportional editing falloff.
   * **(P) Linear**. Equivalent of "Linear" proportional editing falloff.
   * **(P) Constant**. Equivalent of "Constant" proportional editing falloff.

   The default option is **None**.
* **Clamp**. If checked, then the amplitude of attracting force vector will be
  restricted with the distance to attractor object. Unchecked by default.

Outputs
-------

This node has the following outputs:

* **VField**. Vector field of the attracting force.
* **SField**. Scalar field of the attracting force (amplitude of the attracting force).

Examples of usage
-----------------

The attraction field of one point visualized:

.. image:: https://user-images.githubusercontent.com/284644/79471192-b8bba900-801b-11ea-829e-2b003d9000da.png

The attraction field of Z axis visualized:

.. image:: https://user-images.githubusercontent.com/284644/79471186-b78a7c00-801b-11ea-8926-3cc14b792220.png

The attraction field of a point applied to several planes:

.. image:: https://user-images.githubusercontent.com/284644/79471194-b9543f80-801b-11ea-89dc-3b631659f1b2.png

Use the attraction field of cylinder to move points of the plane up:

.. image:: https://user-images.githubusercontent.com/284644/80508641-bcdbb500-8991-11ea-9ed0-030ca6d0bc44.png

