Logic Functions
===============

.. image:: https://user-images.githubusercontent.com/14288520/189692704-621b9c7d-f4a7-4950-9ad0-b44a69ed7162.png
  :target: https://user-images.githubusercontent.com/14288520/189692704-621b9c7d-f4a7-4950-9ad0-b44a69ed7162.png

Functionality
-------------

This node offers a variety of logic gates to evaluate any boolean inputs
It also has different operations to evaluate a pair of numbers, like minor than or greater than.


Input and Output
----------------

Depending on the mode you choose the sockets are automatically changed to
accommodate the expected inputs.
Output is always going to be a boolean.


Parameters
----------

Most operations are self explanatory,
but in case they aren't then here is a quick overview:

=================== ========= ========= =================================
Tables              inputs     type      description
=================== ========= ========= =================================
And                  x, y      integer   True if X and Y are True
Or                   x, y      integer   True if X or Y are True
Nand                 x, y      integer   True if X or Y are False
Nor                  x, y      integer   True if X and Y are False
Xor                  x, y      integer   True if X and Y are opposite
Xnor                 x, y      integer   True if X and Y are equals

If                   x         integer   True if X is True
Not                  x         integer   True if X is False

<                    x, y      float     True if X < Y
>                    x, y      float     True if X > Y
==                   x, y      float     True if X = Y
!=                   x, y      float     True if X not = Y
<=                   x, y      float     True if X <= Y
>=                   x, y      float     True if X >= Y

True                 none      none      Always True
False                none      none      Always False
=================== ========= ========= =================================

Advanced Parameters
-------------------

In the N-Panel (and on the right-click menu) you can find:

* **Output NumPy**: Get NumPy arrays in stead of regular lists (makes the node faster). [Not available for GCD or Round-N]
* **List Match**: Define how list with different lengths should be matched.  [Not available for GCD or Round-N]


Example of usage
----------------

.. image:: https://user-images.githubusercontent.com/14288520/189728289-aa5a39d2-0e99-462f-8eb7-b2a771ee1b10.png
  :target: https://user-images.githubusercontent.com/14288520/189728289-aa5a39d2-0e99-462f-8eb7-b2a771ee1b10.png

In this example we use Logic with Switch Node to choose between two vectors depending on the logic output.
