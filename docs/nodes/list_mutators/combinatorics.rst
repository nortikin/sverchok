Combinatorics
=============

Functionality
-------------

Combinatorics node performs various combinatoric operations like: **Product**, **Permutations** and **Combinations**.


Inputs
------

The inputs to the node are a set of lists of any type and a set of control parameters.

The list inputs in combination to the control parameter inputs (Repeat / Length) are vectorized and the control parameters accept either single or multiple values for vectorization.

List inputs to the node:
- **A**
- **B**  [1]
...
- **Z**  [1]

Notes:
[1] : The multiple list inputs are available for the **Product** operation, all the other operations take one list input. For the **Product** operation as the last list input is connected a new empty input socket will appear to allow other lists to be connected.


Parameters
----------

The **Operation** parameter allows to select one of following operations: Product, Permutations and Combinations.

All parameters except **Operation** can be given as an external input.

+---------------+---------------+----------+--------------------------------------------+
| Param         | Type          | Default  | Description                                |
+===============+===============+==========+============================================+
| **Operation** | Enum:         | Product  | See details in the Operations section.     |
|               |  Product      |          |                                            |
|               |  Permutations |          |                                            |
|               |  Combinations |          |                                            |
+---------------+---------------+----------+--------------------------------------------+
| **Repeat**    | Int           | 1        | Repeat the input lists this many times [1] |
+---------------+---------------+----------+--------------------------------------------+
| **Length**    | Int           | 1        | The number of the elements in the list to  |
|               |               |          | operate on [2]                             |
+---------------+---------------+----------+--------------------------------------------+
| **A**         | List          |          | The list of elements to operate on.        |
+---------------+---------------+----------+--------------------------------------------+
| **B..Z**      | List          |          | Additional lists to operate on [3]         |
+---------------+---------------+----------+--------------------------------------------+

Notes:
[1] : The Repeat parameter is only available for the **Product** operation.
[2] : The Length parameter is only available for the **Permutations** and **Combinations** operation.
[3] : Additional lists inputs are available only for the **Product** operation.

Operations
----------

**Product**

For this operation the node allows an arbitrary number of input lists to be product together as: A x B x .. x Z. The result of the product operation is a list of elements each of size equal to the number of input lists and has all the combinations of elements from the first list, followed by all elements in the second list etc.

e.g. for two connected list inputs:

A : ["X", "Y"]
B : [1, 2, 3]

The result A x B is:

["X", "Y"] x [1, 2, 3] => [ ["X", 1], ["X", 2], ["X", 3], ["Y", 1], ["Y", 2], ["Y", 3] ]

The value of the **Repeat** parameter makes the node compute the product of all the connected lists replicated this number of times.

e.g. for one connected input with repeat value of 2:

A : ["X", "Y"]
Repeat: 2

The result A x A is:

["X", "Y"] x ["X", "Y"] => [ ["X", "X"], ["X", "Y"], ["Y", "X"], ["Y", "Y"] ]


**Permutations**

For this operation the node take a single input list and generates the permutations of its elements. The **Length** parameter sets the number of elements in the list to be permutated.

Notes:
* If the **Length** is zero, the node will permute ALL elements in the list.
* The **Length** value is bounded between zero and the length of the input list, so any length values larger than the length of the input list is equivalent to permuting ALL elements in the list.

e.g. for a list of 3 (mixed) elements:

A: ["X", 3, (1,1,1)]
L: 3

The result is:

[
  ['X', 3, (1, 1, 1)],
  ['X', (1, 1, 1), 3],
  [3, 'X', (1, 1, 1)],
  [3, (1, 1, 1), 'X'],
  [(1, 1, 1), 'X', 3],
  [(1, 1, 1), 3, 'X']
]

**Combinations**

For this operation the node takes a single list as input and generates the combinations of its elements taking L number of elements given by the **Length** parameter.

Notes:
* If the **Length** is zero, the node will combine ALL elements in the list.
* The **Length** value is bounded between zero and the length of the input list, so any length values larger than the length of the input list is equivalent to combining ALL elements.

e.g. for a list of 4 elements taken 2 elements:

A : [1, 'X', (1, 2, 3), [1, 3]]
L : 2

The result is:

[
  [1, 'X'],
  [1, (1, 2, 3)],
  [1, [1, 3]],
  ['X', (1, 2, 3)],
  ['X', [1, 3]],
  [(1, 2, 3), [1, 3]]
]


Outputs
-------

**Result**
The list of product, permutations or combinations.

The results will be generated only when the **Result** output is connected.


