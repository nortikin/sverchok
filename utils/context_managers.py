context_managers.py

from contextlib import contextmanager


@contextmanager
def hard_freeze(self):
    '''
    This prevents properties from calling updateNode when edited. it Freezes the node-tree until control flow leaves the context.
    '''
    self.id_data.freeze(hard=True)
    yield self
    self.id_data.unfreeze(hard=True)
