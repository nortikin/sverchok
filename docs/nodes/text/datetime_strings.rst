Datetime Strings
================

This is a beta node. Please visit  https://github.com/nortikin/sverchok/pull/2137

This node processes dates formatted as text, and lets you convert them into an ordinal (a day indication, an integer). It also supports the subordinal (float, what percent into the day, *seconds / total_seconds_in_day* ).

If you intend to use this node it is important that you absorb the documentation that accompanies the Python datetime module. Especially of interest should be *strptime* and *strftime* and the examples that demonstrate how to interact with string representations of dates.

Features:
--------

- *Ordinal* is an integer representing a day, this is the kind of precision that is useful if you are working on the scale of months, years or decades.

- *Subordinal* is a little bit more precise and gives you the ratio (using seconds) of how far into the day it is. This date information needs hours/minutes/seconds to be provided. Useful for timescales of hours, days or weeks..

Not yet implemented are *Micro-ordinal*, which would take milliseconds into account. Such date information would be useful for plotting sub second timeseries... or multi-second, (but not so handy for multi-minute timeseries, generally)

