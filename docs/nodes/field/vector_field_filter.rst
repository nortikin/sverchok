Vector Field Filter
===================

Functionality
-------------

This node changes vector field so that the new field acts only along chosen coordinates.

Inputs
------

This node has the following inputs:

* **Field**. The vector field to be modified. This input is mandatory.

Parameters
----------

This node has the following parameters:

* **Coordinates**. Type of coordinate system to be used. Available options are:
  Cartesian, Cylindrical and Spherical coordinates. The default value is
  Cartesian.
* **X** / **Y** / **Z**. These parameters are only available when using
  Cartesian coordinate system. Checked parameter means that vector field is
  allowed to act along X / Y / Z axis, coordpondingly.
* **Rho** / **Phi** / **Z**. These parameters are only available when using
  Cylindrical coordinate system. Checked paramter means that vector field is
  allowed to act along corresponding coordinate.
* **Rho** / **Phi** / **Theta**. These parameters are only available when using
  Spherical coordinate system. Checked parameter means that vecotr field is
  allowed to act along cooresponding coordinate.

By default the vector field is allowed to act along all coordinates - i.e. the output vector field is the same as input one.

Outputs
-------

This node has the following outputs:

* **Field**. Restricted vector field.

