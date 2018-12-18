List Statistics
===============

Functionality
-------------

List Statistics node computes various statistical quantities for the values in a list.

Inputs
------

The **Data** input is expected to be a list of integers / floats or list of lists of integers / floats.
All inputs are vectorized.

Parameters
----------

The **Function** parameter allows to select the statistical function to compute the corresponding statistical quantity for the input values.

+----------------+---------------------+---------+------------------------------------------+
| Param          | Type                | Default | Description                              |
+================+=====================+=========+==========================================+
| **Function**   | Enum                | Average | The statistical function applied to      |
|                |  All Statistics     |         | the input values.                        |
|                |  Sum                |         |                                          |
|                |  Sum Of Squares     |         | For "All Statistics" selection the node  |
|                |  Product            |         | computes and outputs the statistical     |
|                |  Average            |         | quantities for all the statistical       |
|                |  Geometric Mean     |         | functions along with their corresponding |
|                |  Harmonic Mean      |         | names.                                   |
|                |  Standard Deviation |         |                                          |
|                |  Root Mean Square   |         |                                          |
|                |  Skewness           |         |                                          |
|                |  Kurtosis           |         |                                          |
|                |  Minimum            |         |                                          |
|                |  Maximum            |         |                                          |
|                |  Median             |         |                                          |
|                |  Percentile         |         |                                          |
|                |  Histogram          |         |                                          |
+----------------+---------------------+---------+------------------------------------------+
| **Percentage** | Float               | 0.75    | The percentage value for the             |
|                |                     |         | percentile function. [1]                 |
+----------------+---------------------+---------+------------------------------------------+
| **Normalize**  | Boolean             | False   | Flag to normalize the histogram bins     |
|                |                     |         | to the given normalize size. [2]         |
+----------------+---------------------+---------+------------------------------------------+
| **Bins**       | Int                 | 10      | The number of bins in the histogram. [2] |
+----------------+---------------------+---------+------------------------------------------+
| **Size**       | Float               | 10.00   | The normalized size of the histogram.[2] |
+----------------+---------------------+---------+------------------------------------------+

Notes:
[1] : The **Percentage** input socket is available only for the **Percentile** function.
[2] : The **Normalize** setting and the **Bins** and **Size** input sockets are available only for the **Histogram** function.

Outputs
-------
**Name(s)**
The name(s) of the statistical value(s) computed corresponding to the selected statistical function.

**Value(s)**
The statistical quantity of the input values corresponding to the selected function. For a vectorized input the output values are a series of quantities corresponding to the selected function.

When "All Statistics" is selected the **Names** and **Values** outputs will list the names and the corresponding values for all the statistical functions.


