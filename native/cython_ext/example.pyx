# Sanity-check module to confirm the Cython build pipeline works.
# Only add real code here after profiling has identified a specific,
# narrow bottleneck that Numba could not handle.

def ping() -> str:
    return "pong from cython"
