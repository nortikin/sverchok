Rotation Field
==============

Functionality
-------------

This node generates a Vector Field which is calculated as
force rotating points around some axis. Several physics-like falloff laws are supported.
Falloffs similar to standard proportional editing mode are supported too (they
are marked with `(P)` in the name).

Inputs
------

This node has the following inputs:

* **Location**. Point on the rotating axis

  It is possible to provide several location points. The default value is `(0, 0, 0)` (origin).

* **Direction**. Direction of the rotation axis.  The default value is `(0, 0, 1)` (Z axis).

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

* **Join mode**. This determines how the distance is calculated when multiple
  attraction centers are provided. The available values are:

  * **Average**. Calculate the average of the attracting forces towards the
    provided centers. This mode is used in physics. This option is the default
    one.
  * **Nearest**. Use only the force of the attraction towards the nearest attraction center.
  * **Separate**. Generate a separate field of attraction force for each attraction center.

   This parameter is not available when the **Attractor type** is set to **Mesh - Faces**.

* **Clamp**. If checked, then the amplitude of attracting force vector will be
  restricted with the distance to attractor object. Unchecked by default.

Outputs
-------

* **VField**. Vector field of the rotating force.

Examples of usage
-----------------

.. image:: https://user-images.githubusercontent.com/10011941/107337942-45f45080-6abb-11eb-8245-74afc5fab5df.png
