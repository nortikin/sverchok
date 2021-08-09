An explanation of Epsilon (and the computational limits imposed by 32bit floating point arithmetic)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

   This explanation is directed at the newcomer, for more elaborate
   explanations consult the links below.

Blender’s ``Vector``
--------------------

A ``float`` is number with a decimal point and one or more digits behind
the decimal point. Blender’s ``Vector`` datatypes are currently *32bit
floats*, the same is true for regular ``Python`` floats. The limit of
the 32bit float precision is approximately 5 to 6 digits of
significance. The reason for this limited precision is purely down to
the amount of memory that 32bit floats are stored in. The choice to use
32bit floats in Blender is about lower memory usage and the non-critical
/ non-engineering “Artistic” nature of Blender’s origins.

Numpy ``datatypes``
-------------------

``Numpy`` offers 32bit and 64bit floats. 64bit floats store more
information (more significant digits) and therefore take up more memory
to store the value. They are a lot more precise.

What does this mean for Sverchok?
---------------------------------

Sverchok uses ``numpy`` extensively, but for some functionality we
import Blender functions and they use ``Vector`` datatypes internally
based around 32bit floats, those functions will have limited internal
precision. To get the most accuracy out of these kinds of calculations
the numbers need to be in the same order of magnitude throughout the
whole calculation. Most users will rarely run into issues, but you might
have if you are reading this.

How does this effect Sverchok? To begin to answer that, some context is needed.
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For example if you have vectors with an ``x`` component of ``4000m``,
then that number is ultimately accurate only to about a centimeter.

.. code:: python

   4000.01

You might see more numbers behind the decimal point, but consider those
an illusion (an artifact) - only the first 5 or 6 numbers in the 32bit
float will be considered significant.

In non-engineering tolerances in the real world what sense does it make
to have a tolerance of centimeters on something that is 4 kilometer
long. Especially if the end product is going to be a render. If you are
rendering something that is 4km long, like a bridge, how many pixels
would the render need to be wide to make a detail (like a weld-seam) of
1 centimeter thick appear in the render? That’s a big render.

If we think more about architectural structures, something like 40
meters, well then the precision behind the decimal is 6-2 = 4, a tenth
of a millimeter. If you are rendering a 40m tall building, how many
pixels would the render need to be high to see a details of a tenth of a
millimeter? That’s a big render, it’s the same as the previous example.

.. code:: python

   40.0001

Calculations and Epsilon
~~~~~~~~~~~~~~~~~~~~~~~~

The core concept is: if your geometry uses big numbers, you can increase
``Epsilon`` to allow the tolerance in the calculations to be more in
line with the magnitude of the numbers. If you have really small numbers
(like millimeters) in your vectors, you want ``epsilon`` to be as small as possible.
