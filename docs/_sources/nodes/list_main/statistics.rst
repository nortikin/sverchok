List Statistics
===============

.. image:: https://user-images.githubusercontent.com/14288520/187748171-58c72008-67ec-4951-9f69-7f0eb1ab6f96.png
    :target: https://user-images.githubusercontent.com/14288520/187748171-58c72008-67ec-4951-9f69-7f0eb1ab6f96.png

Functionality
-------------

List Statistics node computes various statistical quantities for the input values.

Inputs
------

The **Data** input is expected to be a list of integers / floats or list of lists of integers / floats.
All inputs are vectorized.

Parameters
----------

The **Function** parameter allows to select the statistical function to compute the corresponding statistical quantity for the input values.

+----------------+------------------------+---------+-------------------------------------------+
| Param          | Type                   | Default | Description                               |
+================+========================+=========+===========================================+
| **Function**   | Enum                   | Average | The statistical function applied to       |
|                |  * All Statistics      |         | the input values.                         |
|                |  * Selected Statistics |         |                                           |
|                |                        |         |                                           |
|                |  * Sum                 |         |                                           |
|                |  * Sum Of Squares      |         |                                           |
|                |  * Sum Of Inverse      |         | For "All Statistics" selection the node   |
|                |  * Product             |         | computes and outputs the statistical      |
|                |  * Average             |         | quantities for all the statistical        |
|                |  * Geometric Mean      |         | functions along with their corresponding  |
|                |  * Harmonic Mean       |         | names.                                    |
|                |  * Variance            |         |                                           |
|                |  * Standard Deviation  |         |                                           |
|                |  * Standard Error      |         |                                           |
|                |  * Root Mean Square    |         | For "Selected Statistics" selection the   |
|                |  * Skewness            |         | node computes and outputs the statistical |
|                |  * Kurtosis            |         | quantities for the selected statistical   |
|                |  * Minimum             |         | functions along with their corresponding  |
|                |  * Maximum             |         | names.                                    |
|                |  * Range               |         |                                           |
|                |  * Median              |         |                                           |
|                |  * Percentile          |         |                                           |
|                |  * Histogram           |         |                                           |
|                |  * Count               |         |                                           |
+----------------+------------------------+---------+-------------------------------------------+
| **Percentage** | Float                  | 0.75    | The percentage value for the              |
|                |                        |         | percentile function. [1]                  |
+----------------+------------------------+---------+-------------------------------------------+
| **Normalize**  | Boolean                | False   | Flag to normalize the histogram bins      |
|                |                        |         | to the given normalize size. [2]          |
+----------------+------------------------+---------+-------------------------------------------+
| **Bins**       | Int                    | 10      | The number of bins in the histogram. [2]  |
+----------------+------------------------+---------+-------------------------------------------+
| **Size**       | Float                  | 10.00   | The normalized size of the histogram.[2]  |
+----------------+------------------------+---------+-------------------------------------------+

Notes:
[1] : The **Percentage** input socket is available only for the **Percentile** function.
[2] : The **Normalize** setting and the **Bins** and **Size** input sockets are available only for the **Histogram** function.

Extra Parameters
----------------
The Property Panel contains additional settings to configure the statistics drawn in the node editor: font, text color, text scale and floating point precision of the displayed statistics, the x/y offset of the displayed statistics relative to the node and a setting for toggling the statistics names between full names and abbreviations.

The fonts used for this node are monospace fonts for best text alignment.

Outputs
-------
* **Name(s)** The name(s) of the statistical value(s) computed corresponding to the selected statistical function.
* **Value(s)** The statistical quantity of the input values corresponding to the selected function. For a vectorized input the output values are a series of quantities corresponding to the selected function.

When "All Statistics" is selected the **Names** and **Values** outputs will list the names and the corresponding values for all the statistical functions.


Examples
--------

.. image:: https://user-images.githubusercontent.com/14288520/187533079-ada585a4-d1cf-4eb0-ba80-8faae3f53222.png
    :target: https://user-images.githubusercontent.com/14288520/187533079-ada585a4-d1cf-4eb0-ba80-8faae3f53222.png

* Number-> :doc:`Random </nodes/number/random>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

.. image:: https://user-images.githubusercontent.com/14288520/187532896-f7fe6bdd-d25e-40f4-99bf-d2373f75b9c0.png
    :target: https://user-images.githubusercontent.com/14288520/187532896-f7fe6bdd-d25e-40f4-99bf-d2373f75b9c0.png

* Number-> :doc:`Random </nodes/number/random>`
* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

