=======================
Profile Parametric Node
=======================


**Profile Node** implements a useful subset of the SVG path section commands. Currently the following segment types are available:

+---------+------+---------------------------------------------------------------------------------+ 
| name    | cmd  | parameters                                                                      | 
+=========+======+=================================================================================+ 
| MoveTo  | M|m  | <2v coordinate>                                                                 |
+---------+------+---------------------------------------------------------------------------------+ 
| LineTo  | L|l  | <2v coordinate 1> <2v coordinate 2> <2v coordinate n> [z]                       |
+---------+------+---------------------------------------------------------------------------------+ 
| CurveTo | C|c  | <2v control1> <2v control2> <2v knot2> <int num_segments> <int even_spread> [z] |
+---------+------+---------------------------------------------------------------------------------+ 
| ArcTo   | A|a  | <2v rx,ry> <float rot> <int flag1> <int flag2> <2v x,y> <int num_verts> [z]     |
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
    <int .. >
        : means the value will be cast as an int even if you input float
        : flags generally are 0 or 1.
    z   : is optional for closing a line
    X   : as a final command to close the edges (cyclic) [-1, 0]
        in addition, if the first and last vertex share coordinate space
        the last vertex is dropped and the cycle is made anyway.
    #   : single line comment prefix


Variables may be negated, this is a simple negation. There are 2 slightly more elaborate evaluation modes:

**Mode 1:** Requires the use or parentheses to indicate where extra operations take place. Mode 1 is restrictive and only allows addition and subtaction 

::

(a+b-c)

**Mode 2:** Also requires parentheses but allows a more liberal evaluation of operations. Allowed operations are:

::  

(a*b(c/d))

To use Mode 2, you must enable the *extended parsing* switch in the N-panel for the Profile node.


The node started out as a thought experiment and turned into something quite useful, you can see how it evolved in the `github thread <https://github.com/nortikin/sverchok/issues/350>`_
 
Example usage:

.. image:: https://cloud.githubusercontent.com/assets/619340/3905771/193b5d86-22ec-
 11e4-93e5-724863a30bbc.png
 
