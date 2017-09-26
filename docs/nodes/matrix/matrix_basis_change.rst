Matrix Basis Change
===================

Functionality
-------------

Generates the transfomration **matrix** from the XYZ coordinate system to the coordinate system defined by the given TBN (tangent, binormal, normal) vectors. This is essentially known as the change of basis matrix.

The input vectors (TBN) are not required to be ortho-normal. The node will ortho-normalize the resulting vectors as to generate a homogeneous 4x4 matrix (orthonormal rotation matrix + translation). The parameter "Orthogonalizing Order" allows to determine which is the primary, secondary and tertiary orthonormal vectors.

Inputs
------

All inputs are vectorized and they will accept single or multiple values.

- **Location**
- **Tangent**
- **Binormal**
- **Normal**

Parameters
----------

- **Orthogonalizing Order**
- **X**
- **Y**
- **Z**
- **Normalize**

+-------------------------+------------+------------+-----------------------------------------------+
| Param                   |  Type      |  Default   |  Description                                  |
+=========================+============+============+===============================================+
| **Location**            |  Vector    |  (0, 0, 0) |  Location of the system origin                |
+-------------------------+------------+------------+-----------------------------------------------+
| **Tangent**             |  Vector    |  (1, 0, 0) |  The tangent (X') vector in the TBN system    |
+-------------------------+------------+------------+-----------------------------------------------+
| **Binormal**            |  Vector    |  (0, 1, 0) |  The tangent (Y') vector in the TBN system    |
+-------------------------+------------+------------+-----------------------------------------------+
| **Normal**              |  Vector    |  (0, 0, 1) |  The tangent (Z') vector in the TBN system    |
+-------------------------+------------+------------+-----------------------------------------------+


Outputs
-------

**Matrix**, **Orhtonormal X**, **Orhtonormal Y**, **Orhtonormal Z**.
All outputs will be generated when connected.


Example of usage
----------------

