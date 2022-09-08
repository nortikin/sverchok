Fibonacci Sequence
==================

.. image:: https://user-images.githubusercontent.com/14288520/189181489-6896836d-2249-4df1-8651-47752bb9fcaf.png
  :target: https://user-images.githubusercontent.com/14288520/189181489-6896836d-2249-4df1-8651-47752bb9fcaf.png

Functionality
-------------

This node produces specified number of items from Fibonacci sequence::

  1, 1, 2, 3, 5, 8, 13, 21 ...

Each next item is sum of two previous.

This node allows you to specify first two items for your sequence. Note that these numbers can be even negative.

Sequence can be re-scaled so that maximum of absolute values of produced items will be equal to specified value.

Inputs & Parameters
-------------------

All parameters can be given by the node or an external input.
This node has the following parameters:

+----------------+---------------+-------------+----------------------------------------------------+
| Parameter      | Type          | Default     | Description                                        |
+================+===============+=============+====================================================+
| **X1**         | Float         | 1.0         | First item of sequence.                            |
+----------------+---------------+-------------+----------------------------------------------------+
| **X2**         | Float         | 1.0         | Second item of sequence.                           |
+----------------+---------------+-------------+----------------------------------------------------+
| **Count**      | Int           | 10          | Number of items to produce. Minimal value is 3.    |
+----------------+---------------+-------------+----------------------------------------------------+
| **Max**        | Float         | 0.0         | If non-zero, then all output sequence will be      |
|                |               |             | re-scaled so that maximum of absolute values will  |
|                |               |             | be equal to number specified.                      |
+----------------+---------------+-------------+----------------------------------------------------+

Outputs
-------

This node has one output: **Sequence**.

Inputs and outputs are vectorized, so if series of values is passed to one of
inputs, then this node will produce several sequences.

Example of usage
----------------

No scale (max=0). Real Fibonacci values:

.. image:: https://user-images.githubusercontent.com/14288520/189183869-023d705c-a53b-4705-896d-4b7a0d6beec1.png
  :target: https://user-images.githubusercontent.com/14288520/189183869-023d705c-a53b-4705-896d-4b7a0d6beec1.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer 2D </nodes/viz/viewer_2d>`

Rescale to max value:

.. image:: https://user-images.githubusercontent.com/14288520/189183892-b59c5f64-29a0-4caf-8546-3b8f51c0709f.png
  :target: https://user-images.githubusercontent.com/14288520/189183892-b59c5f64-29a0-4caf-8546-3b8f51c0709f.png

* Number-> :doc:`Number Range </nodes/number/number_range>`
* Vector-> :doc:`Vector In </nodes/vector/vector_in>`
* Viz-> :doc:`Viewer 2D </nodes/viz/viewer_2d>`
