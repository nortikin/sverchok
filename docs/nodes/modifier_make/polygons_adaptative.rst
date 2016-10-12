Adaptative Polygons
===================

Functionality
-------------

Share one object to other. Donor spreading himself to recipient polygons. every polygon recieve one object and deform as normals say to him. 

Inputs
------

**VersR** and **PolsR** is Recipient object's data. **VersD** and **PolsD** is donor's object data. **Z_Coef** is coefficient of height, can be vectorized.

Parameters
----------

table

+------------------+---------------+-------------------------------------------------------------------+
| Param            | Type          | Description                                                       |  
+==================+===============+===================================================================+
| **Donor width**  | Float         | Width of spreaded donors is part from recipient's polygon's width | 
+------------------+---------------+-------------------------------------------------------------------+

Outputs
-------

**Vertices** and **Polygons** are data for created object.

Example of usage
----------------

.. image:: https://cloud.githubusercontent.com/assets/5783432/4222738/25e20e00-3916-11e4-9aca-5127f2edaa95.jpg
  :alt: Adaptive_Polygons.jpg

