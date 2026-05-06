"""Add-ons that sit outside the core ExpGym evaluation suite.

Modules in this package are not imported by the core ReAct loop, the
three scenarios, or the CLI. They are example strategies and helpers
that callers can build on or ignore. ``parallel_cache`` is currently
the only module here; it backs the PoolAct strategy reported in the
paper and is normally consumed via ``expgym.poolact``.
"""
