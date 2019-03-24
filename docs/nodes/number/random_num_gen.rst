Random Num Gen
==============


Functionality
-------------

Produces a list of pseudo-random numbers from a seed value.


Inputs & Parameters
-------------------

+----------------+------------------------------------------------------------------------+
| Parameters     | Description                                                            |
+================+========================================================================+
| Int/ Float     | Number type to be created                                              |
+----------------+------------------------------------------------------------------------+
| Size           | Amount of numbers you want to create                                   |
+----------------+------------------------------------------------------------------------+
| Seed           | Accepts float values, they are hashed into *Integers* internally.      |
+----------------+------------------------------------------------------------------------+
| Int/Float Low  | Lower limit of values (included)*                                      |
+----------------+------------------------------------------------------------------------+
| Int/Float High | Higher limit of values (included)*                                     |
+----------------+------------------------------------------------------------------------+
| Weights        | On "Int" mode. Can be supplied to create a non-uniform distribution    |
+----------------+------------------------------------------------------------------------+
| Unique         | On "Int" mode. Outputs non-repeated numbers.                           |
|                | The output size will be limited to (Int High -  Int Low + 1)           |
+----------------+------------------------------------------------------------------------+
| Distribution   | On "Float" mode many distribution functions can be selected.           |
|                | Beta, Binomial, Chi_square, Exponential, F Distrib., Gamma, Geometric, | 
|                | Gumbel, Laplace, Logistic, Log Normal, Log Series, Negative Binomial,  | 
|                | Noncentred Chi-Square, Normal, Pareto, Poisson, Power, RayLeigh,       |
|                | Standard Cauchy, Standard Gamma, Standard T, Triangular, Uniform,      |
|                | Vonmises, Wald, Weibull, Zipf                                          |
+----------------+------------------------------------------------------------------------+
| Alpha          | Distribution parameter. Alpha > 0**                                    |
+----------------+------------------------------------------------------------------------+
| Beta           | Secondary distribution parameter. Beta > 0**                           |
+----------------+------------------------------------------------------------------------+
|  t             | Normalized distribution parameter. 0 < t < 1                           |
+----------------+------------------------------------------------------------------------+

What's a Seed? Read the `Python docs here <https://docs.python.org/3.4/library/random.html>`_.

Learn more about the distribution functions on the `SciPy random reference <https://docs.scipy.org/doc/numpy-1.14.0/reference/routines.random.html>`_.

Outputs
-------

A list, or nested lists.

Notes
-----

Providing a float values as a Seed parameter may be unconventional, if you are uncomfortable with it you 
could place a *FloatToInt* node before the Seed parameter.

(*) Notes on Float Low and Float High
 Except on some distributions (Uniform, Beta and Triangular) the output values are mapped to fit the desired range. Due this mapping there will be at least one value which matches the "Float High" and  another that matches the "Float Low"
(**)Notes on Alpha and Beta values
 - On the "F Distribution" the minimum "Beta" is 0.025 
 - On the "Pareto" distribution the minimum valid "Alpha" is 0.01
 - On the "Standard T" distribution the minimum valid "Alpha" is 0.017
 - On the "Triangular" distribution the "Alpha" parameter has to be greater than the "Float Low" and smaller than the  "Float High".
 - On the "Weibull the minimum valid "Alpha" is 0.0028. 
 - On the "Zipf" distribution the minimum valid "Alpha" has to be bigger than 1.0

Examples
--------
With the "Weighted" distribution you can control the relative probability of each possible solution.

.. image:: https://user-images.githubusercontent.com/10011941/46135042-9816dd00-c244-11e8-80e4-41195b3fbdcd.png
  :alt: Weighted_Distribution1.PNG

.. image:: https://user-images.githubusercontent.com/10011941/46135049-9baa6400-c244-11e8-8cc9-3903e05bcd02.png
  :alt: Weighted_Distribution2.PNG

The distribution functions can lead from the default Uniform to a more organic result (Laplace) or with a desired tendency (Triangular)

.. image:: https://user-images.githubusercontent.com/10011941/46135062-9f3deb00-c244-11e8-9de4-b06c044d5520.png
  :alt: Random_Distribution3.PNG
  
.. image:: https://user-images.githubusercontent.com/10011941/46135077-a82ebc80-c244-11e8-9616-6e8cb7218726.png
  :alt: Random_Distribution4.PNG

The "Unique" toggle will make sure there are not repeated numbers, very usefull with the "List Item Node".

.. image:: https://user-images.githubusercontent.com/10011941/54881844-9e34f180-4e54-11e9-8c92-3eee832c6958.png
  :alt: Random_Distribution_Swerchok_parametric_design_random_sample_unique_example

