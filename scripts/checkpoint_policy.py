"""
Checkpoint approval policy for ICM workflow.
"""

from icmlib import parse_identity, model_rank


# Policy constants
ALL_CHECKPOINTS = {"C1", "C2", "C3", "C4", "C5", "C6", "C7"}

REQUIRED = {
    "T1": {"C1", "C2", "C7"},
    "T2": {"C1", "C2", "C5", "C6", "C7"},
    "T3": ALL_CHECKPOINTS,
    "T4": ALL_CHECKPOINTS,
}

ORCH_OK = {
    "T1": {"C1", "C2", "C7"},
    "T2": {"C5", "C6"},
    "T3": set(),
    "T4": set(),
}

T3_BLOCKING = {"C2", "C3", "C4", "C7"}


def required(cp: str, tier: str) -> bool:
    """
    Determine if a checkpoint is required for a tier.
    - C3 and C4 are always required
    - Otherwise check the tier's REQUIRED set
    - Empty tier means all are required
    """
    if cp in {"C3", "C4"}:
        return True

    if tier == "":
        return True

    return cp in REQUIRED.get(tier, set())


def blocking(cp: str, tier: str) -> bool:
    """
    Determine if a checkpoint blocks progress.
    - Empty tier → True
    - Not required → False
    - T3 → True only if in T3_BLOCKING
    - Otherwise → True
    """
    if tier == "":
        return True

    if not required(cp, tier):
        return False

    if tier == "T3":
        return cp in T3_BLOCKING

    return True


def may_approve(cp: str, tier: str, author: str, approver: str) -> tuple[bool, str]:
    """
    Determine if approver can approve the checkpoint.
    Returns (allowed: bool, reason: str).

    Rules checked in order:
    1. Empty tier → deny "tier not selected"
    2. Helper approver → deny "helpers cannot approve"
    3. Self-approval → deny "no self-approval"
    4. Not required → allow "not required at this tier"
    5. User approver → allow "user approval"
    6. Orchestrator approver → allow if all conditions hold
    7. Otherwise → deny "approver not authorised"
    """
    # Rule 1: Empty tier
    if tier == "":
        return False, "tier not selected"

    # Parse approver identity
    try:
        approver_kind, approver_name, approver_model = parse_identity(approver)
    except ValueError:
        return False, "invalid approver identity"

    # Parse author identity
    try:
        author_kind, author_name, author_model = parse_identity(author)
    except ValueError:
        return False, "invalid author identity"

    # Rule 2: Helper approver
    if approver_kind == "helper":
        return False, "helpers cannot approve"

    # Rule 3: Self-approval
    if author == approver:
        return False, "no self-approval"

    # Rule 4: Not required
    if not required(cp, tier):
        return True, "not required at this tier"

    # Rule 5: User approver
    if approver_kind == "user":
        return True, "user approval"

    # Rule 6: Orchestrator approver
    is_orchestrator = approver_kind == "agent" and approver_name == "orchestrator"
    if is_orchestrator:
        # Check ORCH_OK
        if cp not in ORCH_OK.get(tier, set()):
            return False, f"orchestrator may not approve {cp} at {tier}"

        # Author must be an agent
        if author_kind != "agent":
            return False, "human-authored work needs a user"

        # Model rank check: author <= approver
        author_rank = model_rank(author_model)
        approver_rank = model_rank(approver_model)
        if author_rank > approver_rank:
            return False, "author outranks approver"

        return True, "orchestrator approval"

    # Rule 7: Anything else
    return False, "approver not authorised"


def approver_needed(cp: str, tier: str, author: str) -> str:
    """
    Determine what type of approver is needed.
    Returns: "none", "orchestrator", or "user".

    Logic:
    - Not required → "none"
    - Empty tier → "user"
    - Orchestrator can approve (all conditions) → "orchestrator"
    - Otherwise → "user"
    """
    # Not required
    if not required(cp, tier):
        return "none"

    # Empty tier
    if tier == "":
        return "user"

    # Check if orchestrator can approve
    allowed, _ = may_approve(cp, tier, author, "agent:orchestrator/opus")
    if allowed:
        return "orchestrator"

    return "user"
