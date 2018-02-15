Datetime Strings
================

This is a beta node. Please visit  https://github.com/nortikin/sverchok/pull/2137

This node processes dates formatted as text, and lets you convert them into an ordinal (a day indication, an integer). It also supports the subordinal (float, what percent into the day, *seconds / total_seconds_in_day* ).

If you intend to use this node it is important that you absorb the documentation that accompanies the Python datetime module. Especially of interest should be *strptime* and *strftime* and the examples that demonstrate how to interact with string representations of dates.

Features:
--------

- *Ordinal* is an integer representing a day, this is the kind of precision that is useful if you are working on the scale of months, years or decades.

- *Subordinal* is more precise and gives the ratio (using seconds) of how far into the day it is. This date information needs hours/minutes/seconds to be provided. Useful for timescales of hours, days or weeks..

Not yet implemented are *Micro-ordinal*, which would take milliseconds into account. Such date information would be useful for plotting sub second timeseries... or multi-second, (but not so handy for multi-minute timeseries, generally)

- *N-panel / "Make Reference in Texts"*. is a toggle that creates a Document in the bpy.data.texts called **[DOC] strptime / strftime**, this displays the following reference.

Note: Examples are based (http://strftime.org/ by Will McCutchen) on datetime.datetime(2013, 9, 30, 7, 6, 5)
Python Docs: https://docs.python.org/3.6/library/datetime.html#strftime-and-strptime-behavior

+-----+--------------------------+-----------------------------------------------------------------------------------------------+
|Code | Catches                  | Meaning Example                                                                               |
+=====+==========================+===============================================================================================+
| %a  | Mon                      | Weekday as locale’s abbreviated name.                                                         |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %A  | Monday                   | Weekday as locale’s full name.                                                                |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %w  | 1                        | Weekday as a decimal number, where 0 is Sunday and 6 is Saturday.                             |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %d  | 30                       | Day of the month as a zero-padded decimal number.                                             |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %-d | 30                       | Day of the month as a decimal number. (Platform specific)                                     |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %b  | Sep                      | Month as locale’s abbreviated name.                                                           |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %B  | September                | Month as locale’s full name.                                                                  |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %m  | 09                       | Month as a zero-padded decimal number.                                                        |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %-m | 9                        | Month as a decimal number. (Platform specific)                                                |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %y  | 13                       | Year without century as a zero-padded decimal number.                                         |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %Y  | 2013                     | Year with century as a decimal number.                                                        |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %H  | - 07                     | - Hour (24-hour clock) as a zero-padded decimal number.                                       |
| %-H | - 7                      | - Hour (24-hour clock) as a decimal number. (Platform specific)                               |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %I  | - 07                     | - Hour (12-hour clock) as a zero-padded decimal number.                                       |
| %-I | - 7                      | - Hour (12-hour clock) as a decimal number. (Platform specific)                               |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %p  | AM                       | Locale’s equivalent of either AM or PM.                                                       |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %M  | 06                       | Minute as a zero-padded decimal number.                                                       |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %-M | 6                        | Minute as a decimal number. (Platform specific)                                               |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %S  | 05                       | Second as a zero-padded decimal number.                                                       |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %-S | 5                        | Second as a decimal number. (Platform specific)                                               |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %f  | 000000                   | Microsecond as a decimal number, zero-padded on the left.                                     |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %z  | ?                        | UTC offset in the form +HHMM or -HHMM (empty string if the the object is naive).              |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %Z  | ?                        | Time zone name (empty string if the object is naive).                                         |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %j  | - 273                    | - Day of the year as a zero-padded decimal number.                                            |
| %-j | - 273                    | - Day of the year as a decimal number. (Platform specific)                                    |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %U  | 39                       | Week number of the year (Sunday as the first day of the week) as a zero padded decimal number.|
|     |                          | All days in a new year preceding the first Sunday are considered to be in week 0.             | 
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %W  | 39                       | Week number of the year (Monday as the first day of the week) as a decimal number.            | 
|     |                          | All days in a new year preceding the first Monday are considered to be in week 0.             |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %c  | Mon Sep 30 07:06:05 2013 | Locale’s appropriate date and time representation.                                            |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %x  | - 09/30/13               | - Locale’s appropriate date representation.                                                   |
| %X  | - 07:06:05               | - Locale’s appropriate time representation.                                                   |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
| %%  | %                        | A literal '%' character.                                                                      |
+-----+--------------------------+-----------------------------------------------------------------------------------------------+
