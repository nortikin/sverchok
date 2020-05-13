Range Switch
============

Functionality
-------------

This node set a switch state to ON/OFF based on a driving value relative to a given value range.


Inputs
------

All inputs will accept single or multiple values.

- **Value**
- **Boundary1** [1]
- **Boundary2** [1]

Notes:
[1] : The boundary values do not have to be in increasing order or absolute.


Parameters
----------

The **Mode** parameter allows to select one of the three switch modes: **Inside ON**, **Inside OFF** and **Pass Through**.

- For **Inside ON** mode the switch is ON when the value is inside the boundary range and OFF otherwise.
- For **Inside OFF** mode the switch is OFF when the value is inside the boundary range and ON otherwise.
- For **Pass Through** mode the switch will toggle betwen OFF/ON (or ON/OFF) when the value crosses the range from one side to the other.

    [0]-- outside -->[b1]<-- inside -->[b2]<-- outside --> (+)

    INSIDE ON mode:

    OFF ---> |b1| <-- ON --> |b2| <--- OFF   # inside ON,  outside OFF

    INSIDE OFF mode:

    ON  ---> |b1| <-- OFF --> |b2| <--- ON   # inside OFF, outside ON

    PASS THROUGH mode:

    ON  ---> |b1| -- ON --> |b2| ---> OFF    # passing through range switches state
    ON  <--- |b1| <- OFF -- |b2| <--- OFF    #

+------------------+---------------+--------------+----------------------------------+
| Param            | Type          | Default      | Description                      |
+==================+===============+==============+==================================+
| **Mode**         | Enum          | Pass Through | The switching mode  [1]          |
|                  |  Inside ON    |              |                                  |
|                  |  Inside OFF   |              |                                  |
|                  |  Pass Through |              |                                  |
+------------------+---------------+--------------+----------------------------------+
| **Value**        | Float         | 1.0          | The driving value of the switch  |
+------------------+---------------+--------------+----------------------------------+
| **Boundary1**    | Float         | 2.0          | The first boundary of the range  |
+------------------+---------------+--------------+----------------------------------+
| **Boundary2**    | Float         | 3.0          | The second boundary of the range |
+------------------+---------------+--------------+----------------------------------+

Notes:
[1] : When the mode is **Pass Through** a "Toggle State" button becomes available to allow you to set the initial state of the switch.


Outputs
-------
Outputs will be generated when connected.

**State**
This output is the current state of the switch. (ON = True, OFF = False)

**Zone**
This output is the number of the zone (1,2,3) the driving value is in relative to the boundary values.

Zone 1 (BELOW)  for value < min(b1,b2)
Zone 2 (INSIDE) for min(b1,b2) <= value <= max(b1,b2)
Zone 3 (ABOVE)  for max(b1,b2) < value


Example of usage
----------------

