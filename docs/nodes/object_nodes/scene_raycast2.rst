Scene Raycast
=============

Functionality
-------------
This node casts single ray from point in direction defined by **origin** and **direction**
inputs respectively. Then it checks collision of this ray with any object in the scene
and returns information about collision.

Inputs
------
**origin** - origin point of casted ray.

**direction** - direction of casted ray.

Parameters
----------

Outputs
-------
**HitP** - Single point. Coordinate where casted ray is colliding with object.

**HitNorm** - Vector of length 1 unit. Normal of the object polygon that colliding with a ray.

**success** - bool value, *True* if ray collided with anything, else is *False*

**FaceINDEX** - Integer value. Index of object face, that colliding with a ray.

**Objects** - ID of object that colliding with a ray. String with format
*bpy.data.objects['Name of Object']*

**hited object matrix** - matrix of object that colliding with a ray.

Example of usage
----------------
