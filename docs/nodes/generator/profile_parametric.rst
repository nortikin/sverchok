=======================
Profile Parametric Node
=======================


**Profile Node** implements a useful subset of the SVG path section commands. Currently the following segment types are available:

+---------+------+---------------------------------------------------------------------------------+ 
| name    | cmd  | parameters                                                                      | 
+=========+======+=================================================================================+ 
| MoveTo  | M,  m| <2v coordinate>                                                                 |
+---------+------+---------------------------------------------------------------------------------+ 
| LineTo  | L,  l| <2v coordinate 1> <2v coordinate 2> <2v coordinate n> [z]                       |
+---------+------+---------------------------------------------------------------------------------+ 
| CurveTo | C,  c| <2v control1> <2v control2> <2v knot2> <int num_verts> <int even_spread> [z]    |
+---------+------+---------------------------------------------------------------------------------+ 
| ArcTo   | A,  a| <2v rx,ry> <float rot> <int flag1> <int flag2> <2v x,y> <int num_verts> [z]     |
+---------+------+---------------------------------------------------------------------------------+ 
| Close   | X    |                                                                                 |  
+---------+------+---------------------------------------------------------------------------------+ 
| comment | #    | must be first thing on the line, no trailing comment instructions.              | 
+---------+------+---------------------------------------------------------------------------------+ 

::

    <>  : mandatory field
    []  : optional field
    2v  : two point vector `a,b`
            - no space between ,
            - no backticks
            - a and b can be 
                - number literals
                - lowercase 1-character symbols for variables
    int : means the value will be cast as an int even if you input float
          flags generally are 0 or 1.
    z   : is optional for closing a line
    X   : as a final command to close the edges (cyclic) [-1, 0]
          in addition, if the first and last vertex share coordinate space
          the last vertex is dropped and the cycle is made anyway.
    #   : single line comment prefix


**Mode 0:** default behaviour, variables may be negated

:: 

    M a,-a
    L a,a -a,a -a,-a z

There are 2 slightly more elaborate evaluation modes:

**Mode 1:** Requires the use or parentheses to indicate where extra operations take place. 
Mode 1 is restrictive and only allows addition and subtraction 

::

(a+b-c)

**Mode 2:** Also requires parentheses but allows a more liberal evaluation of operations. Allowed operations are:

::  

(a*b(c/d))

To use Mode 2, you must enable the *extended parsing* switch in the N-panel for the Profile node.


Examples
--------

If you have experience with SVG paths most of this will be familiar. The biggest difference is that only the
LineTo command accepts many points, and we always start the profile with a M <pos>,<pos>.

::

    M 0,0
    L a,a b,0 c,0 d,d e,-e 
    

CurveTo and ArcTo only take enough parameters to complete one Curve or Arc, 
unlike real SVG commands which take a whole sequence of chained CurveTo or ArcTo commands. The decision to keep 
it at one segment type per line is mainly to preserve readability.

The CurveTo and ArcTo segment types allow you to specify how many vertices are used to generate the segment. SVG 
doesn't let you specify such things, but it makes sense to allow it for the creation of geometry.

the fun bit about this is that all these variables / components can be dynamic

::

    M 0,0
    L 0,3 2,3 2,4
    C 2,5 2,5 3,5 10 0
    L 5,5
    C 7,5 7,5 7,3 10 0
    L 7,2 5,0
    X
    
or

::

    M a,a
    L a,b c,b -c,d
    C c,e c,e b,e g 0
    L e,e
    C f,e f,e f,-b g 0
    L f,c e,a
    X


More Info
---------

The node started out as a thought experiment and turned into something quite useful, you can see how it evolved in the `github thread <https://github.com/nortikin/sverchok/issues/350>`_
 
Example usage:

.. image:: https://cloud.githubusercontent.com/assets/619340/3905771/193b5d86-22ec-11e4-93e5-724863a30bbc.png
 

.. image:: https://cloud.githubusercontent.com/assets/619340/3895396/81f3b96c-224d-11e4-9ca7-f07756f40a0e.png


Gotchas
-------

The update mechanism doesn't process inputs or anything until the following conditions are satisfied:

 * Profile Node has at least one input socket connected
 * The file field on the Node points to an existing Text File.


Keyboard Shortcut to refresh Profile Node
-----------------------------------------

Updates made to the profile path text file are not propagated automatically to any nodes that might be reading that file. 
To refresh a Profile Node simply hit ``Ctrl+Enter`` In TextEditor while you are editing the file, or click one of the 
inputs or output sockets of Profile Node. There are other ways to refresh (change a value on one of the incoming nodes, 
or clicking the sockets of the incoming nodes)

