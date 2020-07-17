Sun Position
============

Dependencies
------------


This node requires Ladybug_ library to work.

.. _Ladybug: https://github.com/ladybug-tools/ladybug

Functionality
-------------

Calculates sun position in a given time and location

Inputs
------

- **Location**: Geographic location (from Location node or from EPW file).
- **Month**: Month of the year.
- **Day**: Day of the month
- **Hour**: Hour of the day

Options
-------

- **Sun Distance**: Distance in the representation of the Sun.
- **North Angle**: Angle of the north direction with the Y axis.

Outputs
-------

- **Altitude**: Sun Altitude.
- **Azimuth**: Sun Azimuth.
- **Sun Position**: Matrix to place a Sun Light in the Scene.

Examples
--------

.. image:: https://user-images.githubusercontent.com/10011941/81987066-44cfe900-9639-11ea-91bd-147b0a752031.png
