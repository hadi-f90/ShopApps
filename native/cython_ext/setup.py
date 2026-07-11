from setuptools import setup
from Cython.Build import cythonize

setup(
    name="._native",
    ext_modules=cythonize("example.pyx", language_level=3),
)
