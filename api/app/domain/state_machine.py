"""
State machine and lifecycle transition rules for Requests and Deployments.
"""

from api.app.domain.models import DeploymentStatus, RequestStatus


class InvalidStateTransitionError(Exception):
    """Raised when an illegal lifecycle state jump is attempted."""

    pass


class TerminalStateError(InvalidStateTransitionError):
    """Raised when attempting to transition out of a terminal state."""

    pass


class DeploymentLockedError(Exception):
    """Raised when a deployment already has an active, non-terminal lifecycle request."""

    pass


# Valid Request state transitions
_REQUEST_TRANSITIONS: dict[RequestStatus, set[RequestStatus]] = {
    RequestStatus.PENDING: {
        RequestStatus.DISPATCHED,
        RequestStatus.FAILED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.DISPATCHED: {
        RequestStatus.PLANNING,
        RequestStatus.APPLYING,
        RequestStatus.FAILED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.PLANNING: {
        RequestStatus.AWAITING_APPROVAL,
        RequestStatus.APPLYING,
        RequestStatus.FAILED,
        RequestStatus.CANCELLED,
    },
    RequestStatus.AWAITING_APPROVAL: {
        RequestStatus.APPLYING,
        RequestStatus.CANCELLED,
        RequestStatus.FAILED,
    },
    RequestStatus.APPLYING: {
        RequestStatus.VALIDATING,
        RequestStatus.SUCCEEDED,
        RequestStatus.FAILED,
    },
    RequestStatus.VALIDATING: {
        RequestStatus.SUCCEEDED,
        RequestStatus.FAILED,
    },
    # Terminal states: no further transitions allowed
    RequestStatus.SUCCEEDED: set(),
    RequestStatus.FAILED: set(),
    RequestStatus.CANCELLED: set(),
}

# Valid Deployment state transitions
_DEPLOYMENT_TRANSITIONS: dict[DeploymentStatus, set[DeploymentStatus]] = {
    DeploymentStatus.PENDING: {
        DeploymentStatus.PROVISIONING,
        DeploymentStatus.FAILED,
    },
    DeploymentStatus.PROVISIONING: {
        DeploymentStatus.ACTIVE,
        DeploymentStatus.FAILED,
    },
    DeploymentStatus.ACTIVE: {
        DeploymentStatus.DESTROYING,
    },
    DeploymentStatus.DESTROYING: {
        DeploymentStatus.DESTROYED,
        DeploymentStatus.FAILED,
    },
    DeploymentStatus.FAILED: {
        DeploymentStatus.DESTROYING,  # Allow cleanup / destroy of failed deployment
        DeploymentStatus.PROVISIONING,  # Allow retry
    },
    # Terminal state: no further transitions allowed
    DeploymentStatus.DESTROYED: set(),
}

_TERMINAL_REQUEST_STATUSES: set[RequestStatus] = {
    RequestStatus.SUCCEEDED,
    RequestStatus.FAILED,
    RequestStatus.CANCELLED,
}

_TERMINAL_DEPLOYMENT_STATUSES: set[DeploymentStatus] = {
    DeploymentStatus.DESTROYED,
}


def is_terminal_request_status(status: RequestStatus) -> bool:
    """Check if request status is terminal."""
    return status in _TERMINAL_REQUEST_STATUSES


def is_terminal_deployment_status(status: DeploymentStatus) -> bool:
    """Check if deployment status is terminal."""
    return status in _TERMINAL_DEPLOYMENT_STATUSES


def validate_request_transition(current: RequestStatus, target: RequestStatus) -> None:
    """
    Validate if transitioning from current to target status is permitted.
    Raises TerminalStateError or InvalidStateTransitionError on invalid transition.
    """
    if current == target:
        return  # Idempotent no-op

    if is_terminal_request_status(current):
        raise TerminalStateError(
            f"Cannot transition request from terminal state '{current}' to '{target}'."
        )

    allowed = _REQUEST_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Illegal request state transition from '{current}' to '{target}'."
        )


def validate_deployment_transition(current: DeploymentStatus, target: DeploymentStatus) -> None:
    """
    Validate if transitioning deployment from current to target status is permitted.
    Raises TerminalStateError or InvalidStateTransitionError on invalid transition.
    """
    if current == target:
        return  # Idempotent no-op

    if is_terminal_deployment_status(current):
        raise TerminalStateError(
            f"Cannot transition deployment from terminal state '{current}' to '{target}'."
        )

    allowed = _DEPLOYMENT_TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidStateTransitionError(
            f"Illegal deployment state transition from '{current}' to '{target}'."
        )
