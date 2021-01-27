Switch
======

.. image:: https://user-images.githubusercontent.com/28003269/71510839-aae5ea80-28a9-11ea-8511-a185fe337206.png

Functionality
-------------

Switches between to sets of inputs. Also can work as filter.

Category
--------

Logic -> Switch

Inputs
------

- **State** - True or False (0 or 1)
- **A_0 - 10** - True, False or None
- **B_0 - 10** - True, False or None


Outputs
-------

- **Out_0 - 10** - result of switching between two values

Parameters
----------

+--------------------------+-------+--------------------------------------------------------------------------------+
| Parameters               | Type  | Description                                                                    |
+==========================+=======+================================================================================+
| in/out number (N panel)  | 0 - 10| Number of socket sets                                                          |
+--------------------------+-------+--------------------------------------------------------------------------------+

Usage
-----

**Generation of bool sequence easily:**

.. image:: https://user-images.githubusercontent.com/28003269/39827448-f8d6c08c-53c8-11e8-864e-b72afd67befb.png

**Working with different types of data:**

.. image:: https://user-images.githubusercontent.com/28003269/39925828-3fc466fe-553e-11e8-861e-f3e3dfbfc92a.png

**It is possible to deal with empty objects:**

.. image:: https://user-images.githubusercontent.com/28003269/39926724-225bc0b4-5541-11e8-974f-6efebb68392e.png

**Using as filter:**

.. image:: https://user-images.githubusercontent.com/28003269/39926961-dccbb1f2-5541-11e8-8337-281510eec5d8.png

It has supporting of numpy arrays. Output is related with input from socket A and socket B. 
Output will be numpy array if at least one input sockets (A or B) has numpy array and another socket does not have 
list with two or more values.

.. image:: https://user-images.githubusercontent.com/28003269/69896932-219cd000-135e-11ea-9e99-93def391466b.png

**Alternative of list mask out node:**

.. image:: https://user-images.githubusercontent.com/28003269/69903773-791b5a00-13b7-11ea-8210-0c73a46cae77.png

Working inside and outside of object level
------------------------------------------

Something unexpected can be with none iterable objects like matrix or Blender objects. 
On the picture below it can be expected that switch should add first matrix and second quaternion:

.. image:: https://user-images.githubusercontent.com/28003269/69897081-1054c300-1360-11ea-80de-0aac8f310633.png

but for this states input should have values on first object level not on second data level:

.. image:: https://user-images.githubusercontent.com/28003269/69897085-38dcbd00-1360-11ea-8939-b6910445e5eb.png