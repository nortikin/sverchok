# SPDX-License-Identifier: GPL-3.0-or-later
from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class RaggedArray:
    """Polygon indices as two numeric arrays, including mixed-size ngons."""

    indices: np.ndarray
    offsets: np.ndarray

    def __post_init__(self):
        indices = np.asarray(self.indices, dtype=np.intp)
        offsets = np.asarray(self.offsets, dtype=np.intp)
        if indices.ndim != 1 or offsets.ndim != 1 or not len(offsets):
            raise ValueError('RaggedArray needs flat indices and nonempty offsets')
        if offsets[0] != 0 or offsets[-1] != len(indices) or np.any(np.diff(offsets) < 0):
            raise ValueError('Invalid polygon offsets')
        object.__setattr__(self, 'indices', indices)
        object.__setattr__(self, 'offsets', offsets)

    @classmethod
    def from_rows(cls, rows):
        if isinstance(rows, cls):
            return rows
        if isinstance(rows, np.ndarray) and rows.ndim == 2:
            count, width = rows.shape
            return cls(rows.reshape(-1), np.arange(count+1, dtype=np.intp)*width)
        lengths = np.fromiter((len(row) for row in rows), dtype=np.intp, count=len(rows))
        offsets = np.r_[0, np.cumsum(lengths, dtype=np.intp)]
        indices = np.concatenate([np.asarray(row, dtype=np.intp) for row in rows]) if offsets[-1] else np.empty(0, dtype=np.intp)
        return cls(indices, offsets)

    def __len__(self):
        return len(self.offsets)-1

    def __getitem__(self, index):
        if index < 0:
            index += len(self)
        if index < 0 or index >= len(self):
            raise IndexError(index)
        return self.indices[self.offsets[index]:self.offsets[index+1]]

    def __iter__(self):
        return (self[index] for index in range(len(self)))

    def to_list(self):
        return [row.tolist() for row in self]
