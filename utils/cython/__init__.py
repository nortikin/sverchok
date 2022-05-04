IS_COMPILED = True

try:
    from . import mesh
except ModuleNotFoundError:
    IS_COMPILED = False
