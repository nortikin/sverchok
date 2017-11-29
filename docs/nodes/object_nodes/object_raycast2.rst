Object ID Raycast
=================

Functionality
-------------
This node casts single ray from point in direction defined by **origin** and **direction**
inputs respectively. Then it checks collision only with selected object or objects
and returns information about collision.

Inputs
------
**Object** - object or list of objects which node will check on collision with ray.

**origin** - origin point of casted ray.

**direction** - direction of casted ray.

Parameters
----------

Outputs
-------
**success** - Bool value. *True* if ray collided with object, else is *False*.

**HitP** - Single point. Coordinate where casted ray colliding with object.

**HitNorm** - Vector of length 1 unit. Normal of the object polygon that colliding with a ray.

**FaceINDEX** - Integer value. Index of object face, that colliding with a ray.

Example of usage
----------------
