
Solid
-----

A Solid is a mathematical object, which is defined and represented by its boundaries (BRep)

Solids are heavier to compute than meshes but they do not depend on topology and they are better for a Boolean workflow (Union, Intersection and Difference)

In Sverchok solids depend on FreeCAD_ to work (that depends on OpenCascade) because Blender does not provide a internal way of handling this kind of objects.

.. _FreeCAD: https://www.freecadweb.org/

**Installation**

A python 3.7 FreeCAD is needed. a windows version can be found here https://github.com/sgrogan/FreeCAD/releases/tag/PY3.7-win

Then the path to the FreeCAD "bin" folder has to be placed in the Sverchok Preferences ->Extra-Nodes ->FreeCad-> TextField and click on Set Path. Then re-start Blender and it should be working.

If you change the folder, copy the new path and click  "Reset Path".

.. image:: https://user-images.githubusercontent.com/10011941/85948130-55b98d00-b94f-11ea-8727-16e35cb551bd.png

Sverchok provides a special Solids Menu by pressing "Shift + S"
