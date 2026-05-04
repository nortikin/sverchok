Symmetrize Curve
================

Functionality
-------------

This node performs operation similar to "Symmetrize Mesh" node, but works with
Curve objects instead of meshes.
In general, the node cuts the curve in half by a plane, takes one half, and
mirrors it relative to the same plane. After that, in some cases it makes sense
to reverse the direction of mirrored curve. And after that, the node optionally
can concatenate the original part of curve with it's mirrored counterpart, at
least in cases when they meet exactly.
It may be that the mirror plane does not intersect the curve at all. In such a
case, the node will just return the original curve together with it's mirrored
copy.

Inputs
------

This node has the following inputs:

* **Curve**. The curve to be symmetrized. This input is mandatory.
* **Point**. This input is available only when the **Direction** paramter is
  set to **Custom**. This defines the point on the plane which is used as a
  mirror. The default value is ``(0,0,0)`` (origin).
* **Normal**. This input is available only when the **Direction** parameter is
  set to **Custom**. This defines the normal of the plane which is used as a
  mirror. The default value is ``(0,0,1)`` (Z axis).

Parameters
----------

This node has the following parameters:

- **Direction**. Transformation direction. This defines which part of the curve which be taken and where it will be mirrored to. The following directions are available:

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

- **Output mode**. The following options are available:

  - **Concatenate**. If selected, then the node will try to concatenate parts
    of the original curve to their mirrored counterparts, if they meet with
    specified precision (and their directions are matching - i.e., the end of
    one part is coinciding with the beginning of another one). Selected by
    default.
  - **Output pairs**. For each segment of original curve, the node will output a
    list of 2 items: the original segment and it's mirrored version.
  - **Sequential**. For each original curve, the node will output a single list
    of all segments: original ones and mirrored ones.
  - **Separate outputs**. Two node outputs will be used: **OriginalCurve** and
    **MirroredCurve**. The first output will contain all segments of original
    curve, and the second will contain all mirrored segments.

- **Reverse**. If checked, then the node will reverse the direction of
  mirrorred parts of the curve. This is not available when **Output mode**
  parameter is set to **Concatenate**, because it is assumed to be always
  checked in such situations: without reversing the mirrorred parts of the
  curve it would not be possible to concatenate them to original parts. Checked
  by default.
- **Use NURBS algorithm**. This parameter is available in the N panel only. If
  checked, the node will use special case of it's algorithm for NURBS and
  NURBS-like curves; in such cases, the resulting curves will be also NURBS.
  Otherwise, the node will always use a generic version of the algorithm; in
  such a case, the resulting curve will be a generic Curve object even if the
  original curve was NURBS-like. Also, this parameter may impact performance
  significantly; but which option is faster depends on exact nature of the
  curve being processed; sometimes the NURBS algorithm is several times faster,
  sometimes it's the other way around. Checked by default.
- **Accuracy**. This parameter is available in the N panel only. Accuracy level
  both for algorithm which finds the intersection of the curve with the mirror
  plane, and for checking whether the original part of the curve meets with
  it's mirrored counterpart precisely enough to be concatenated. The number of
  exact digits after decimal point is specified. The default value is 6.

Outputs
-------

This node has the following output:

- **Curve**. The resulting symmetrized curve. This output is used when **Output
  mode** parameter is set to a value other than **Separate outputs**.
- **OriginalCurve**. Segments of original curve. This output is used when
  **Output mode** parameter is set to **Separate outputs**.
- **MirroredCurve**. Mirrored curve segments. This output is used when **Output
  mode** parameter is set to **Separate outputs**.

Examples of Usage
-----------------

Simple example of usage with Concatenate mode. The orange curve is the original one:

.. image:: https://github.com/user-attachments/assets/b8f3b0b9-d4cb-49aa-b0cd-9af3c7ca8e6d
  :target: https://github.com/user-attachments/assets/b8f3b0b9-d4cb-49aa-b0cd-9af3c7ca8e6d

Here Sequential mode (without concatenation) is used, but then the "Snap NURBS
curves" node is used to adjust the tangents of the curve, and then the curve is
concatenated manually:

.. image:: https://github.com/user-attachments/assets/f420ab64-8b11-4056-a886-78a75627dc94
  :target: https://github.com/user-attachments/assets/f420ab64-8b11-4056-a886-78a75627dc94

Separate Outputs mode can be used, for example, with "Ruled Surface" node:

.. image:: https://github.com/user-attachments/assets/fbeda9c9-4743-41fc-93fb-ebd9d663d62e
  :target: https://github.com/user-attachments/assets/fbeda9c9-4743-41fc-93fb-ebd9d663d62e

