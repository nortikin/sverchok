List Match
==========

Great node to cut and extend lists to maximal or minimal length for one of them.


Functionality
-------------


Getting multiple inputs node get length for all lists and define maximal/minimal of them.


Inputs
------


* **data** multisocket


Parameters
----------


* **Level**: level of data

  Next you choose case of matching, two lines are:

  **recursive** - recursive case of matching (not working now)
  
  **final** - usual job on defined level  


* **Short**: cut all to minimal length of lists
* **Cycle**: extend all to maximal length of lists by cyclingly repeating
* **Repeat**: extend all to maximal length of lists by last item repeating
* **X-Ref**: extend all to maximal length of lists by multiplying lengths,

  i.e. [0,1] and [4,5,6] will give [0,1,0,1,0,1] and [4,4,5,5,6,6] in output


Outputs
-------

* **data** adaptable socket


Examples
--------

* **Initial:**

  [0, 1] & [0, 1, 2, 3, 4]

* **Short:**

  [0, 1] & [0, 1]

* **Cycle:**

  [0, 1, 0, 1, 0] & [0, 1, 2, 3, 4]

* **Repeat:**

  [0, 1, 1, 1, 1] & [0, 1, 2, 3, 4]

* **X-Ref:**

  [0, 1, 0, 1, 0, 1, 0, 1, 0, 1] & [0, 0, 1, 1, 2, 2, 3, 3, 4, 4]


