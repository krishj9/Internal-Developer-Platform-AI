"""
Domain Arithmetic Tools for the Math Reasoning Agent.

These tools provide deterministic mathematical operations that the agent invokes
via Gemini Function Calling rather than relying on probabilistic mental arithmetic.
"""

from collections.abc import Callable
from typing import Any


def add(a: float, b: float) -> float:
    """
    Calculate the sum of two numbers (a + b).

    Args:
        a: The first number.
        b: The second number to add.

    Returns:
        The sum of a and b.
    """
    return float(a + b)


def subtract(a: float, b: float) -> float:
    """
    Calculate the difference between two numbers (a - b).

    Args:
        a: The number to subtract from (minuend).
        b: The number being subtracted (subtrahend).

    Returns:
        The difference resulting from subtracting b from a.
    """
    return float(a - b)


def multiply(a: float, b: float) -> float:
    """
    Calculate the product of two numbers (a * b).

    Args:
        a: The first factor.
        b: The second factor.

    Returns:
        The product of a and b.
    """
    return float(a * b)


def divide(a: float, b: float) -> float:
    """
    Calculate the quotient of two numbers (a / b).

    Args:
        a: The dividend (number being divided).
        b: The divisor (number to divide by). Must not be zero.

    Returns:
        The quotient resulting from dividing a by b.

    Raises:
        ValueError: If b is zero.
    """
    if b == 0:
        raise ValueError("Cannot divide by zero.")
    return float(a / b)


# Tool registry mapping tool function names to callable functions
MATH_TOOL_REGISTRY: dict[str, Callable[..., Any]] = {
    "add": add,
    "subtract": subtract,
    "multiply": multiply,
    "divide": divide,
}

# Declarative tool schemas for Gemini Function Calling
MATH_TOOLS_LIST = [add, subtract, multiply, divide]
