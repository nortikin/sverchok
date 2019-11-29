Vector Math Node
----------------

This is a versatile node. You can perform 1 operation on 1000's of
list-elements, or perform operations pairwise on two lists of 1000's of
elements, even if they are nested. It is therefore what we call
a *Vectorized* node, for an elaborate explanation of what this
means see this [introduction]().

The node expects correct input for the chosen operation (called mode),
but it will fail gracefully with a message in the console if the input
is not right for the selected mode.

The node will accept lists of NumPy arrays. Flat arrays for scalar lists
and two axis arrays for vectors with shape [n,3]

It can also output Numpy arrays in the same format when using the NumPy
implementation and the "Output NumPy" parameter activated.
(See advanced parameters)

Input and Output
^^^^^^^^^^^^^^^^

========= ==========================================================
socket    description
========= ==========================================================
inputs    Expect a Vector and Scalar (v,s), or two Vectors (u, v)
outputs   Will output a Scalar (s), or a Vector (w).
========= ==========================================================

Depending on the mode you choose the sockets are automatically changed to
accommodate the expected inputs and outputs types


Modes
^^^^^

Most operations are self explanatory,
but in case they aren't then here is a quick overview:

=================== ========= ========= =========================================
Tables              inputs    outputs   description
=================== ========= ========= ========================================
Scale YZ             v, s     w         scale vector by amount
Scale XZ             v, s     w         scale vector by amount
Scale XY             v, s     w         scale vector by amount
Cross product        u, v     s         u cross v
Dot product          u, v     s         u dot v
Add                  u, v     w         u + v
Sub                  u, v     w         u - v
Length               u        s         distance(u, origin)
Distance             u, v     s         distance(u, v)
Normalize            u        w         scale vector to length 1
Negate               u        w         reverse sign of components
Project              u, v     w         u project v
Reflect              u, v     w         u reflect v
Multiply Scalar      u, s     w         multiply(vector, scalar)
Multiply 1/Scalar    u, s     w         multiply(vector, 1/scalar)
Angle Degrees        u, v     s         angle(u, origin, v)
Angle Radians        u, v     s         angle(u, origin, v)
Round s digits       u, s     v         reduce precision of components
Component-wise U*V   u, v     w         `w = (u.x*v.x, u.y*v.y, u.z*v.z)`
Scalar to X          v,s      w         replace x with the scalar
Scalar to Y          v,s      w         replace y with the scalar
Scalar to Z          v,s      w         replace z with the scalar
Switch X             u,v      w         replace the X value of u with X value o v
Switch Y             u,v      w         replace the X value of u with X value o v
Switch Z             u,v      w         replace the X value of u with X value o v
Swap XY              u        w         swaps the X value with the Y value
Swap XZ              u        w         swaps the X value with the Z value
Swap YZ              u        w         swaps the Y value with the Z value
=================== ========= ========= =========================================

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

**Implementation**: MathUtils or NumPy. NumPy is the default and is usually faster.

**Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). [Not available in the MathUtils implementation]
