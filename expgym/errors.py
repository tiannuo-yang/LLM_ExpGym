"""Explicit model-input failures, distinct from evaluator infrastructure errors.

Only raise these exceptions while validating a model-supplied payload. Missing
data, malformed backend results, and tool implementation failures must propagate
as their original exceptions rather than becoming observations or zero scores.
"""


class ToolInputError(ValueError):
    """The model supplied invalid syntax, fields, or values to a tool."""


class InvalidConfigurationError(ToolInputError):
    """A submitted tuning configuration is invalid, not a backend failure."""
