Symmetrize Solid
================

Functionality
-------------

This node performs operation similar to "Symmetrize Mesh" node, but works with
Solid objects instead of meshes.
In general, the node cuts the Solid object in half by a plane, takes one half,
mirrors it relative to the same plane, and fuses original part with the
mirrored part.

**Note**: Unfortunately, due to specifics of how FreeCAD booleans work, in some
cases this node can produce weird (or even empty) results when **Merge** mode
is enabled.

Inputs
------

This node has the following inputs:

* **Solid**. The Solid object to be symmetrized. This input is mandatory.
* **Point**. This input is available only when the **Direction** paramter is
  set to **Custom**. This defines the point on the plane which is used as a
  mirror. The default value is ``(0,0,0)`` (origin).
* **Normal**. This input is available only when the **Direction** parameter is
  set to **Custom**. This defines the normal of the plane which is used as a
  mirror. The default value is ``(0,0,1)`` (Z axis).

Parameters
----------

This node has the following parameters:

- **Direction**. Transformation direction. This defines which part of the Solid
  object which be taken and where it will be mirrored to. The following
  directions are available:

   - **-X to +X**
   - **+X to -X**
   - **-Y to +Y**
   - **+Y to -Y**
   - **-Z to +Z**
   - **+Z to -Z**
   - **Custom**. The mirroring plane will be defined by **Point** and
     **Normal** inputs. The node will take the half of space where negative
     direction of the normal points to, and mirror it into the part where the
     normal points to.

  The default direction is **-X to +X**.

- **Merge Solids**. If checked, then mirrored parts of the solid will be merged
  with original parts into a single Solid object. Otherwise, two separate
  objects will be produced. Checked by default.

Outputs
-------

This node has the following outputs:

- **Solid**. The resulting Solid objects.

Examples of Usage
-----------------

Example 1: Symmetrize from +Z to -Z:

.. image:: https://github.com/user-attachments/assets/bb6dd0fc-301b-45ca-8caa-ced38a4e65dc
  :target: https://github.com/user-attachments/assets/bb6dd0fc-301b-45ca-8caa-ced38a4e65dc

Example 2: Symmetrize relative to custom plane.

.. image:: https://github.com/user-attachments/assets/0285ff78-31b5-48a2-a96a-76d7365756fc
  :target: https://github.com/user-attachments/assets/0285ff78-31b5-48a2-a96a-76d7365756fc

