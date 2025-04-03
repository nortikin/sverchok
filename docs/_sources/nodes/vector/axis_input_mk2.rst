Vector X | Y | Z
================

.. image:: https://user-images.githubusercontent.com/14288520/189370754-8f8083e2-75b9-4c55-af21-a7bda06349af.png
  :target: https://user-images.githubusercontent.com/14288520/189370754-8f8083e2-75b9-4c55-af21-a7bda06349af.png

Functionality
-------------

Sometimes a Vector is needed which only has a value in one of the 3 axes. For instance the rotation vector of the *Matrix In* node. Or the Axis parameter in the *Lathe Node*. Instead of using a *Vector* Node it can be useful to add this Node instead, which lets you easily toggle between::

    X = 1, 0, 0
    Y = 0, 1, 0
    Z = 0, 0, 1

The added bonus is that the minimized state of the Node can show what type of Vector it represents.

.. image:: https://user-images.githubusercontent.com/14288520/189370094-f76392f3-4540-4c50-b27d-feac04b567a6.png
  :target: https://user-images.githubusercontent.com/14288520/189370094-f76392f3-4540-4c50-b27d-feac04b567a6.png

* Text-> :doc:`Stethoscope </nodes/text/stethoscope_v28>`

Parameters
----------

A toggle between ``X | Y | Z``


Outputs
-------

A single Vector output, only ever::

    (1,0,0) or (0,1,0) or (0,0,1)


Examples
--------

`issue tracker thread <https://github.com/nortikin/sverchok/pull/303>`_ 