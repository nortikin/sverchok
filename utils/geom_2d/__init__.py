"""
Idea of this package is creating some basic low level geometric algorithms which are not represented by Blender API.
It would be nice to keep this package without any dependencies or has them as less as possible
even without Blender `mathutils` and other libraries.

According that fact that all algorithms can have changes during all time of development
it is wise to use unit tests for all high level functions which are called by nodes of Sverchok.
New tests can be added to this file: sverchok.tests.geom_2d_tests

After changes which can impact on several algorithm tests of the package should be done.
Run strings below from blender text editor and check result in console.

from sverchok.utils.testing import run_test_from_file
run_test_from_file("geom_2d_tests.py")


There is known problem of intersection algorithm which is main in the library:
1. Robustness: the algorithm dose not have any solution of this problem.
   If initial mesh has very close edges to each other intersection algorithm can fail or give wrong output
   This relates with precision of float number.
2. Performance: on my machine finding of 50000 intersection takes over 2,5 minutes what is very slow.
   Probably using numpy can improve algorithm slightly but it looks like that it can be efficiently adopted
   to the algorithm and will give small improvements. Another solution can be to use another low level
   language like C++ or using such project as Numba what is hardly possible because of adding dependencies
   to Sverchok.
"""
