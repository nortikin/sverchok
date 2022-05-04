import sys
from setuptools import setup, Extension
from Cython.Build import cythonize

v = sys.version_info
if v.major != 3 or v.minor != 10:
    print(f"ERROR: You are using Python{v.major}.{v.minor} version, Python3.10 is required")
    sys.exit()


# https://packaging.python.org/en/latest/guides/packaging-binary-extensions/
# https://setuptools.pypa.io/en/latest/deprecated/distutils/setupscript.html#describing-extension-modules
extensions = [
    Extension(
        "mesh",
        ["src/mesh.pyx", "src/cpp/implementation.cpp"],
        language="c++",
        # extra_compile_args=['-fopenmp'],  # for parallelism https://cython.readthedocs.io/en/latest/src/userguide/parallelism.html#compiling
        # extra_link_args=['-fopenmp'],  # for parallelism
        extra_compile_args=['/std:c++17', '/openmp'],  # for parallelism
        extra_link_args=['/openmp'],  # for parallelism
        include_dirs=[r'E:\blender-git\blender\source\blender\makesdna']
        ),
]


setup(
    name='Hello world app',
    ext_modules=cythonize(
        extensions,
        annotate=True,
        language_level=3,
        ),
    zip_safe=False,
)
