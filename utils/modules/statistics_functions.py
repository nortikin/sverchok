# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

from functools import reduce
from math import sqrt, floor
import sys


def get_sum(values):
    return sum(values)


def get_sum_of_squares(values):
    return sum([v * v for v in values])


def get_sum_of_inversions(values):
    return sum([1.0 / v for v in values])


def get_product(values):
    return reduce((lambda x, y: x * y), values)


def get_average(values):
    return sum(values) / len(values)


def get_geometric_mean(values):
    return pow(get_product(values), 1.0 / len(values))


def get_harmonic_mean(values):
    return len(values) / get_sum_of_inversions(values)


def get_standard_deviation(values):
    a = get_average(values)
    return sqrt(sum([(v - a)**2 for v in values]))


def get_root_mean_square(values):
    return sqrt(get_sum_of_squares(values) / len(values))


def get_skewness(values):
    a = get_average(values)
    n = len(values)
    s = get_standard_deviation(values)
    return sum([(v - a)**3 for v in values]) / n / pow(s, 3)


def get_kurtosis(values):
    a = get_average(values)
    n = len(values)
    s = get_standard_deviation(values)
    return sum([(v - a)**4 for v in values]) / n / pow(s, 4)


def get_minimum(values):
    return min(values)


def get_maximum(values):
    return max(values)


def get_median(values):
    sortedValues = sorted(values)
    index = int(floor(len(values) / 2))
    print("index=", index)
    if len(values) % 2 == 0:  # even number of values ? => take the average of central values
        median = (sortedValues[index - 1] + sortedValues[index]) / 2
    else:  # odd number of values ? => take the central value
        median = sortedValues[index]

    return median


def get_percentile(values, percentage):
    sortedValues = sorted(values)
    index = int(min(int(floor(len(values) * percentage)), len(values) - 1))
    return sortedValues[index]


def get_histogram(values, numBins, normalize=False, normalizedSize=10):
    minValue = get_minimum(values)
    maxValue = get_maximum(values)

    binSize = max((maxValue - minValue) / numBins, sys.float_info.min)

    # initialize the histogram bins
    histogram = [0] * numBins

    # populate the histogram bins
    for i in range(len(values)):
        binIndex = int(min(int(floor((values[i] - minValue) / binSize)), numBins - 1))
        histogram[binIndex] = histogram[binIndex] + 1

    # normalize histogram ?
    if normalize:
        binMax = max(histogram)
        for i in range(len(histogram)):
            histogram[i] = histogram[i] / binMax * normalizedSize

    return histogram
