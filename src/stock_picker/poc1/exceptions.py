class RunBudgetExceeded(RuntimeError):
    """Raised when wall-clock or estimated spend exceeds run_budget."""


class HandoffValidationError(ValueError):
    """Raised when a node output fails Pydantic validation after bounded repair."""
