Quaternion Math Node
--------------------

The Quaternion Math node performs various artithmetic operations on quaternions.

The available arithmetic operations and their corresponding inputs/outputs are:

+============+========+========+=====================================+
| Operation  | Input  | Output | Description                         |
+============+========+========+=====================================+
| ADD        |   NQ   |   Q    | Add multiple quaternions            |
| SUB        |   QQ   |   Q    | Subtract two quaternions            |
| MULTIPLY   |   NQ   |   Q    | Multiply multiple quaternions       |
| DIVIDE     |   QQ   |   Q    | Divide two quaternions              |
| ROTATE     |   QQ   |   Q    | Rotate a quaternion around another  |
| DOT        |   QQ   |   S    | Dot product two quaternions         |
| DISTANCE   |   QQ   |   S    | Distance between two quaternions    |
| NEGATE     |   Q    |   Q    | Negate a quaternion                 |
| CONJUGATE  |   Q    |   Q    | Conjugate a quaternion              |
| INVERT     |   Q    |   Q    | Invert a quaternion                 |
| NORMALIZE  |   Q    |   Q    | Normalize a quaternion              |
| SCALE      |   QS   |   Q    | Scale a quaternion by given factor  |
| QUADRANCE  |   Q    |   S    | Quadrance of a quaternion           |
| MAGNITUDE  |   Q    |   S    | Magnitude of a quaternion           |
+============+========+========+=====================================+

where:

NQ = arbitrary number of quaternion inputs
QQ = two quaternion inputs
Q  = one quaternion input
QS = one quaternion + scalar value
S  = scalar value

For the operations that take multiple quaternion inputs (NQ & QQ) the node provides a PRE / POST option, which lets the node execute the operation on the quaternion inputs in a direct or reverse order. The exceptions to this rule are the ADD, DOT and DISTANCE operations for which the order of quaternions is irrelevant.

For quaternion inputs A and B:
PRE  = A op B
POST = B op A


Inputs
======
The input to the node are lists of quaternions as well as control parameters (like scale etc). For certain operations the node takes arbitrary number of quaternion input lists, for others it takes only two quaternion input lists and for some only one quaternion input list.

The inputs accept single value quaternions or a list of quaternions. The node is vectorized so it will extend the quaternion lists to match the longest input.


Operations
==========

* ADD : adds the components of two or more quaternions

q1 = (w1, x1, y1, z1)
q2 = (w2, x2, y2, z2)

q1 + q2 = (w1 + w2, x1 + x2, y1 + y2, z1 + z1)


* SUB : subtracts the components of two quaternions

q1 = (w1, x1, y1, z1)
q2 = (w2, x2, y2, z2)

q1 - q2 = (w1 - w2, x1 - x2, y1 - y2, z1 - z2)


* MULTIPLY : multiplies two or more quaternions

q1 = (w1, x1, y1, z1) = (w1, V1), where V1 = (x1, y1, z1)
q2 = (w2, x2, y2, z2) = (w2, V2), where V2 = (x2, y2, z2)

q1 x q2 = (w1 * w2 - V1 * V2, w1 * V1 + w2 * V2 + V1 x V2)

where V1 * V2 is dot product of vectors V1 & V2
and V1 x V2 is the cross product of vectors V1 & V2


* DIVIDE : divide two quaternions (multiply one quaternion with inverse of the other)

q1 = (w1, x1, y1, z1)
q2 = (w2, x2, y2, z2)

q1 / q2 = q1 x inverse(q2)


* ROTATE : rotates one quaternion around the other quaternion


* DOT : the dot product of two quaternions

q1 = (w1, x1, y1, z1)
q2 = (w2, x2, y2, z2)

q1 * q2 = w1 * w2 + x1 * x2 + y1 * y2 + z1 * z2


* DISTANCE : the distance between two quaternions

q1 = (w1, x1, y1, z1)
q2 = (w2, x2, y2, z2)

Distance(q1, q2) = Magnitude(q1 - q2)


* NEGATE : negates a quaternion

q = (w, x, y, z)

Negate(q) = (-w, -x, -y, -z)


* CONJUGATE : conjugates a quaternion

q = (w, x, y, z)

Conjugate(q) = (w, -x, -y, -z)


* INVERT : inverts a quaternion

q = (w, x, y, z)

Inverse(q) = Conjugate(q) / Magnitude(q)^2


* NORMALIZE : normalizes a quaternion

q = (w, x, y, z)

Normalize(q) = (w/m, x/m, y/m, z/m)

where m = Magnitude(q)


* SCALE : scales the components of a quaternion

q = (w, x, y, z)

s - (float) the scale factor
sf = (sw, sx, sy, sz) - (array of bools) filters which component is scaled

S = (s if sw else 1, s if sx else 1, s if sy else 1, s if sz else 1)

scale(q, S) = (w * Sw, x * Sx, y * Sy, z * Sz)


* QUADRANCE : the quadreance of a quaternion

q = (w, x, y, z)

Quadrance(q) = w * w + x * x + y * y + z * z

Note: essentially this is the dot product of the quaternion with itself, and also equal to square of the magnitude.

* MAGNITUDE : the magnitude of a quaternion

q = (w, x, y, z)

Magnitude(q) = sqrt(w * w + x * x + y * y + z * z)

Note: this is essentially the square root of the quadrance (the length of the quaternion).


Output
======

**Quaternions** or **Values**
Depending on the operation the output to the node is either a quaternion list or scalar value list.

The node computes the results (quaternions or scalar values) only when the output socket is connected.

