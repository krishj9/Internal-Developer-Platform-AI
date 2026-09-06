"""
Unit tests for Request and Deployment lifecycle state machine transitions.
"""

import pytest

from api.app.domain.models import DeploymentStatus, RequestStatus
from api.app.domain.state_machine import (
    InvalidStateTransitionError,
    TerminalStateError,
    is_terminal_deployment_status,
    is_terminal_request_status,
    validate_deployment_transition,
    validate_request_transition,
)


def test_valid_request_lifecycle_progression():
    # PENDING -> DISPATCHED -> PLANNING -> APPLYING -> VALIDATING -> SUCCEEDED
    validate_request_transition(RequestStatus.PENDING, RequestStatus.DISPATCHED)
    validate_request_transition(RequestStatus.DISPATCHED, RequestStatus.PLANNING)
    validate_request_transition(RequestStatus.PLANNING, RequestStatus.APPLYING)
    validate_request_transition(RequestStatus.APPLYING, RequestStatus.VALIDATING)
    validate_request_transition(RequestStatus.VALIDATING, RequestStatus.SUCCEEDED)


def test_request_idempotent_same_state_transition():
    # Same state is a valid no-op
    validate_request_transition(RequestStatus.PLANNING, RequestStatus.PLANNING)
    validate_request_transition(RequestStatus.APPLYING, RequestStatus.APPLYING)


def test_invalid_request_jump_raises_error():
    with pytest.raises(InvalidStateTransitionError, match="Illegal request state transition"):
        validate_request_transition(RequestStatus.PENDING, RequestStatus.SUCCEEDED)

    with pytest.raises(InvalidStateTransitionError, match="Illegal request state transition"):
        validate_request_transition(RequestStatus.PLANNING, RequestStatus.VALIDATING)


def test_terminal_request_state_cannot_transition():
    assert is_terminal_request_status(RequestStatus.SUCCEEDED) is True
    assert is_terminal_request_status(RequestStatus.FAILED) is True
    assert is_terminal_request_status(RequestStatus.CANCELLED) is True
    assert is_terminal_request_status(RequestStatus.PLANNING) is False

    with pytest.raises(TerminalStateError, match="terminal state 'SUCCEEDED'"):
        validate_request_transition(RequestStatus.SUCCEEDED, RequestStatus.APPLYING)

    with pytest.raises(TerminalStateError, match="terminal state 'FAILED'"):
        validate_request_transition(RequestStatus.FAILED, RequestStatus.DISPATCHED)


def test_valid_deployment_lifecycle_progression():
    # PENDING -> PROVISIONING -> ACTIVE -> DESTROYING -> DESTROYED
    validate_deployment_transition(DeploymentStatus.PENDING, DeploymentStatus.PROVISIONING)
    validate_deployment_transition(DeploymentStatus.PROVISIONING, DeploymentStatus.ACTIVE)
    validate_deployment_transition(DeploymentStatus.ACTIVE, DeploymentStatus.DESTROYING)
    validate_deployment_transition(DeploymentStatus.DESTROYING, DeploymentStatus.DESTROYED)


def test_deployment_terminal_state_cannot_transition():
    assert is_terminal_deployment_status(DeploymentStatus.DESTROYED) is True
    assert is_terminal_deployment_status(DeploymentStatus.ACTIVE) is False

    with pytest.raises(TerminalStateError, match="terminal state 'DESTROYED'"):
        validate_deployment_transition(DeploymentStatus.DESTROYED, DeploymentStatus.ACTIVE)


def test_invalid_deployment_jump_raises_error():
    with pytest.raises(InvalidStateTransitionError, match="Illegal deployment state transition"):
        validate_deployment_transition(DeploymentStatus.PENDING, DeploymentStatus.ACTIVE)
