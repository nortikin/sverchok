Range Integer
=============

Functionality
-------------

*alias: List Range Int*

Useful for generating sequences of Integer values. The code perhaps describes best what the two modes do::

    def intRange(start=0, step=1, stop=1):
        '''
        "lazy range"
        - step is always |step| (absolute)
        - step is converted to negative if stop is less than start
        '''
        if start == stop:
            return []
        step = max(step, 1)
        if stop < start:
            step *= -1
        return list(range(start, stop, step))


    def countRange(start=0, step=1, count=10):
        count = max(count, 0)
        if count == 0:
            return []
        stop = (count*step) + start
        return list(range(start, stop, step))


Inputs
------


Parameters
----------


Outputs
-------

Examples
--------




