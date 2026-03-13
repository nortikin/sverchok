Scalar Math
===========

.. image:: https://user-images.githubusercontent.com/14288520/189060032-dcbef5e5-05da-4b6e-8e45-9926e72e5dc0.png
  :target: https://user-images.githubusercontent.com/14288520/189060032-dcbef5e5-05da-4b6e-8e45-9926e72e5dc0.png

.. image:: https://user-images.githubusercontent.com/14288520/189060063-894e9fb9-9ce1-4683-b5a1-37df332d33aa.png
  :target: https://user-images.githubusercontent.com/14288520/189060063-894e9fb9-9ce1-4683-b5a1-37df332d33aa.png

Functionality
-------------

This node can transform incoming values by a selected function (trigonometric,
or other mathematical function, and also provide some useful math constants)

Inputs & Parameters
-------------------

.. image:: https://user-images.githubusercontent.com/14288520/189060093-98879685-76e8-48eb-8a42-a8ba4158ca13.png
  :target: https://user-images.githubusercontent.com/14288520/189060093-98879685-76e8-48eb-8a42-a8ba4158ca13.png

**float** or **int**

This node will accept lists of flat NumPy arrays [Not available for GCD or Round-N]

+---------------+---------------------------------------------+
| **class**     | **type**                                    |
+---------------+---------------------------------------------+
| Trig          | * Sine, Cosine, Tangent                     |
|               | * Arcsin, Arccosine, Arctangent, atan2,     |
|               | * acosh, asinh                              |
|               | * sinh, cosh, tanh                          |
|               | * Sin(x*y), Cos(x*y)                        |
|               | * y * sin(x), y * cos(x)                    |
|               |                                             |
+---------------+---------------------------------------------+
| Math          | * Add, Sub, Multiply, Divide, Int Division  |
|               | * Squareroot, Exponent, Power y, Power 2    |
|               | * Log, Log10, Log1p                         |
|               | * Absolute, Negate                          |
|               | * Ceiling, Floor                            |
|               | * Min, Max                                  |
|               | * Round, Round N                            |
|               | * Fmod, Modulo                              |
|               | * Mean                                      |
|               | * GCD (Greatest Common Divisor)             |
|               | * Degrees, Radians                          |
|               | * pi * x, tau * x, e * x, phi * x           |
|               | * x + 1, x - 1, x * 2, x / 2                |
|               | * 1 / x                                     |
|               | * tau * (x-1 /x)                            |
|               | * Power y (signed)                          |
+---------------+---------------------------------------------+
| constants     | pi, e, phi, tau.                            |
+---------------+---------------------------------------------+

Advanced Parameters
-------------------

.. image:: https://user-images.githubusercontent.com/14288520/189060741-53d8c63e-c7b5-47cb-9aa7-c7c5c6a7bd1a.png
  :target: https://user-images.githubusercontent.com/14288520/189060741-53d8c63e-c7b5-47cb-9aa7-c7c5c6a7bd1a.png

In the N-Panel (and on the right-click menu) you can find:

* **Input 1 Type**: offers int / float selection for socket 1.
* **Input 2 Type**: offers int / float selection for socket 2.
* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). [Not available for GCD or Round-N]
* **List Match**: Define how list with different lengths should be matched.  [Not available for GCD or Round-N]


Outputs
-------

**float** or **int**
