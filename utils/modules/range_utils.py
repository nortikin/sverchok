# This file is part of project Sverchok. It's copyrighted by the contributors
# recorded in the version control history of the file, available from
# its original location https://github.com/nortikin/sverchok/commit/master
#
# SPDX-License-Identifier: GPL3
# License-Filename: LICENSE

def frange(start, stop, step):
    '''Behaves like range but for floats'''
    if start == stop:
        stop += 1
    step = max(1e-5, abs(step))
    if start < stop:
        while start < stop:
            yield start
            start += step
    else:
        step = -abs(step)
        while start > stop:
            yield start
            start += step


def frange_count(start, stop, count):
    ''' Gives count total values in [start,stop] '''
    # we are casting to int here because the input can be floats.

    if count < 2:
        yield start
    elif start == stop:
        for i in range(int(count)):
            yield start
    else:
        count = int(count)
        step = (stop - start) / (count - 1)
        yield start
        for i in range(count - 2):
            start += step
            yield start
        yield stop


def frange_step(start, step, count):
    ''' Gives count values with step from start'''
    if abs(step) < 1e-5:
        for i in range(int(count)):
            yield start
    else:
        for i in range(int(count)):
            yield start
            start += step
