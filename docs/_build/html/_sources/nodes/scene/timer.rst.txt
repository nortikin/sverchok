Timer
=====

Functionality
-------------

This node helps with managing time, particularly useful for animations.
It provides a set of (internal/external) operations that allow to control timing.
The suppported operations are: Stop, Start, Pause, Reset, Expire, Loop Backward and Loop Forward.

The the node measures time is in seconds and it is based on Blender timeline's time, so the measured time depends on on frame changes in the timeline as well as the frame rate. Because this is tied to Blender's timeline, starting the timer will not measure any time unless the Blender's timeline changes (either via playback, timeline scrubbing or other methods of changing the frame). Scrubbing the timeline back and forth will also affect the timer node's measured time. When scrubbing backwards, the recorded time will also go backwards (assuming the timer is started).

Note: The timer node does not record negative times. Going backward in time (either via backward playback or scrubbing the timeline backwards) will decrease the measured time down to zero and the timer will stop.


Inputs
------

All inputs accept single or multiple values. When any of the node's inputs take multiple values the node creates multiple timers with different settings, which can be controlled collectively via the node's IU (internal operations) or they can be controlled individually via the external operations.

- **Duration**
- **Speed**
- **Loops**
- **Operation** [1]

Notes:
[1] : The operation is a value between 0-6, used to control the timer externally by other nodes.


Operations
----------
Same set of operations are supported internally (via node's UI) or externally via **Operations** input socket.

Supported operations:
+-----------------+-----------------+
| Operation       |  External Value |
+=================+=================+
| STOP            |  0              |
+-----------------+-----------------+
| START           |  1              |
+-----------------+-----------------+
| PAUSE           |  2              |
+-----------------+-----------------+
| RESET           |  3              |
+-----------------+-----------------+
| EXPIRE          |  4              |
+-----------------+-----------------+
| LOOP BACKWARD   |  5              |
+-----------------+-----------------+
| LOOP FORWARD    |  6              |
+-----------------+-----------------+

Note: when an operation is given externally it is only executed if different than the previously executed external operation. This way, during playback if the nodes gets the same value (e.g. 1 = START) every frame, the (START) operation is only executed once.


The Time Slider
---------------
The node has a time slider that can be used to set the timers current time (as a percentage of the timer's duration). This allows the timer to go back and forth in time without playing back the Blender's timeline and it can be useful to set a particular starting time or to test the output of the timer, hence the animationt the timer controls. (the speed option is in this case ignored, since the user controls the speed of time flow via scrubbing the time slider).


Parameters
----------

+--------------------+--------+-----------+--------------------------------------------------+
| Param              |  Type  |  Default  |  Description                                     |
+====================+========+===========+==================================================+
| **Normalize Time** |  Bool  |  False    |  When this is ON the times are given as a        |
|                    |        |           |  percentage of the timer duration [0-1]          |
+--------------------+--------+-----------+--------------------------------------------------+
| **Duration**       |  Float |  10.0     |  Duration after which the timer loops or expires |
+--------------------+--------+-----------+--------------------------------------------------+
| **Speed**          |  Float |  1.0      |  Multiplier for the timer time increment         |
+--------------------+--------+-----------+--------------------------------------------------+
| **Loops**          |  Int   |  0        |  Number of loops after which the timer expires.  |
|                    |        |           |  (0 = No Loops)                                  |
+--------------------+--------+-----------+--------------------------------------------------+


Extra Parameters
----------------
Property Panel has some extra parameters to adjust the timer node behavior for all of its timers.

+---------------+--------+-----------+---------------------------------------------------+
| Param         |  Type  |  Default  |  Description                                      |
+===============+========+===========+===================================================+
| **Absolute**  |  Bool  |  False    |  When this is ON the node measures time relative  |
|               |        |           |  to the frame at which the timer was started.     |
|               |        |           |  When this is OFF the node measures time relative |
|               |        |           |  to the last frame the timer was updated          |
+---------------+--------+-----------+---------------------------------------------------+
| **Sticky**    |  Bool  |  False    |  When this is ON the timer will stay STOPPED once |
|               |        |           |  it stopped or EXPIRED once it expired when the   |
|               |        |           |  timeline is scrubbed, otherwises will unstop or  |
|               |        |           |  unexpire as the timeline is scrubbed             |
+---------------+--------+-----------+---------------------------------------------------+


Outputs
-------

All outputs will be generated when connected.

**Status**
The current status of the timer.

The list of timer status are:
STARTED
STOPPED
PAUSED
EXPIRED


**Elapsed Time**
The elapsed time of the timer. If the **Normalize Time** is enabled, this output will be a value between 0 and 1, otherwise it is a value between 0 and timer's duration.


**Remaining Time**
The remaining time of the timer. If the **Normalize Time** is enabled, this output will be a value between 1 and 0, otherwise it is a value between timer's duration and 0.


**Expired**
This outputs True if the timer expired, otherwise False.

Note: When the node takes multiple inputs with different duration values (creating multiple timers), each timer could expire at different times based on when each timer is started (note that multiple timers can be operated all at once using the node controls (stop/start/pause/reset/expire) or they can be operated using external operations (0-6), in which case each timer could also be started/stopped at different times.

Note: It's also possible to have mutiple timers start at different times and expire later at the same time.

One useful case for this output is that you can chain timer nodes and have one timer, upon expiration, trigger the starting of another timer.


**Loop**
This outputs how many times the timer has looped since it started (a value in between 0 and **Loops** number).



Example of usage
----------------

