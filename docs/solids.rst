
Solid
-----

A Solid is a mathematical object, which is defined and represented by its boundaries (BRep)

Solids are heavier to compute than meshes but they do not depend on topology and they are better for a Boolean workflow (Union, Intersection and Difference)

In Sverchok solids depend on FreeCAD to work (that depends on OpenCascade) because Blender does not provide a internal way of handling this kind of objects.

**Installation**

A python 3.7 FreeCad is needed. a windows version can be found here https://github.com/sgrogan/FreeCAD/releases/tag/PY3.7-win

Then the path to the FreeCad "bin" folder has to be placed in the Sverchok Preferences ->Extra-Nodes ->FreeCad-> TextField and click on Set Path. Then re-start Blender and it should be working
