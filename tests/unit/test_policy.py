"""
Tests for checkpoint_policy module.
"""

import sys
from pathlib import Path
import unittest

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

from checkpoint_policy import required, blocking, may_approve, approver_needed


TIERS = ["", "T1", "T2", "T3", "T4"]
CHECKPOINTS = ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]
AUTHORS = [
    "agent:client-liaison/haiku",
    "agent:issue-clerk/sonnet",
    "agent:orchestrator/opus",
    "user:user1",
]
APPROVERS = [
    "user:user1",
    "user:user2",
    "helper:helper1",
    "agent:orchestrator/opus",
    "agent:issue-clerk/sonnet",
]


# --- Expected-value functions, built independently from the contract's prose ---

EXPECTED_REQUIRED = {
    "T1": {"C1", "C2", "C3", "C4", "C7"},
    "T2": {"C1", "C2", "C3", "C4", "C5", "C6", "C7"},
    "T3": {"C1", "C2", "C3", "C4", "C5", "C6", "C7"},
    "T4": {"C1", "C2", "C3", "C4", "C5", "C6", "C7"},
}

EXPECTED_T3_BLOCKING = {"C2", "C3", "C4", "C7"}

EXPECTED_ORCH_OK = {
    "T1": {"C1", "C2", "C7"},
    "T2": {"C5", "C6"},
    "T3": set(),
    "T4": set(),
}

MODEL_RANK = {"haiku": 1, "sonnet": 2, "opus": 3}


def expected_required(cp, tier):
    if tier == "":
        return True
    return cp in EXPECTED_REQUIRED[tier]


def expected_blocking(cp, tier):
    if tier == "":
        return True
    if not expected_required(cp, tier):
        return False
    if tier == "T3":
        return cp in EXPECTED_T3_BLOCKING
    return True


def _identity(s):
    """Minimal, independent identity parser: (kind, name, model)."""
    kind, rest = s.split(":", 1)
    if kind in ("user", "helper"):
        return kind, rest, ""
    name, model = rest.split("/", 1)
    return kind, name, model


def expected_may_approve(cp, tier, author, approver):
    """Returns (allowed, reason) per the contract's ordered rules."""
    # 1. Empty tier
    if tier == "":
        return False, "tier not selected"

    approver_kind, approver_name, approver_model = _identity(approver)
    author_kind, author_name, author_model = _identity(author)

    # 2. Helper approver
    if approver_kind == "helper":
        return False, "helpers cannot approve"

    # 3. Self-approval
    if approver == author:
        return False, "no self-approval"

    # 4. Not required at this tier — applies to every approver, including
    #    the orchestrator, since rules are checked strictly in order.
    if not expected_required(cp, tier):
        return True, "not required at this tier"

    # 5. User approver
    if approver_kind == "user":
        return True, "user approval"

    # 6. Orchestrator approver
    if approver_kind == "agent" and approver_name == "orchestrator":
        if cp not in EXPECTED_ORCH_OK[tier]:
            return False, f"orchestrator may not approve {cp} at {tier}"
        if author_kind != "agent":
            return False, "human-authored work needs a user"
        if MODEL_RANK.get(author_model, 99) > MODEL_RANK.get(approver_model, 99):
            return False, "author outranks approver"
        return True, "orchestrator approval"

    # 7. Anything else
    return False, "approver not authorised"


def expected_approver_needed(cp, tier, author):
    if not expected_required(cp, tier):
        return "none"
    if tier == "":
        return "user"
    allowed, _ = expected_may_approve(cp, tier, author, "agent:orchestrator/opus")
    if allowed:
        return "orchestrator"
    return "user"


class TestRequired(unittest.TestCase):
    """Test the required() function."""

    def test_c3_c4_always_required(self):
        """C3 and C4 are required at every tier."""
        for tier in ["", "T1", "T2", "T3", "T4"]:
            self.assertTrue(required("C3", tier))
            self.assertTrue(required("C4", tier))

    def test_t1_required(self):
        """T1 requires C1, C2, C3, C4, C7."""
        required_set = {"C1", "C2", "C3", "C4", "C7"}
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertEqual(required(cp, "T1"), cp in required_set)

    def test_t2_required(self):
        """T2 requires C1, C2, C3, C4, C5, C6, C7."""
        required_set = {"C1", "C2", "C3", "C4", "C5", "C6", "C7"}
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertEqual(required(cp, "T2"), cp in required_set)

    def test_t3_all_required(self):
        """T3 requires all checkpoints."""
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertTrue(required(cp, "T3"))

    def test_t4_all_required(self):
        """T4 requires all checkpoints."""
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertTrue(required(cp, "T4"))

    def test_empty_tier_all_required(self):
        """Empty tier requires all checkpoints."""
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertTrue(required(cp, ""))


class TestBlocking(unittest.TestCase):
    """Test the blocking() function."""

    def test_empty_tier_always_blocking(self):
        """Empty tier makes everything blocking."""
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertTrue(blocking(cp, ""))

    def test_not_required_not_blocking(self):
        """Non-required checkpoints are not blocking."""
        # C5, C6 not required at T1
        self.assertFalse(blocking("C5", "T1"))
        self.assertFalse(blocking("C6", "T1"))

    def test_t3_blocking_rules(self):
        """T3: C2, C3, C4, C7 block; C1, C5, C6 don't block (non-required don't block)."""
        self.assertTrue(blocking("C2", "T3"))
        self.assertTrue(blocking("C3", "T3"))
        self.assertTrue(blocking("C4", "T3"))
        self.assertTrue(blocking("C7", "T3"))
        self.assertFalse(blocking("C5", "T3"))
        self.assertFalse(blocking("C6", "T3"))
        self.assertFalse(blocking("C1", "T3"))

    def test_t1_blocking_rules(self):
        """T1 required are all blocking."""
        self.assertTrue(blocking("C1", "T1"))
        self.assertTrue(blocking("C2", "T1"))
        self.assertTrue(blocking("C3", "T1"))
        self.assertTrue(blocking("C4", "T1"))
        self.assertTrue(blocking("C7", "T1"))
        self.assertFalse(blocking("C5", "T1"))
        self.assertFalse(blocking("C6", "T1"))

    def test_t2_all_blocking(self):
        """T2 requires all, so all block."""
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertTrue(blocking(cp, "T2"))

    def test_t4_all_blocking(self):
        """T4 requires all, so all block."""
        for cp in ["C1", "C2", "C3", "C4", "C5", "C6", "C7"]:
            self.assertTrue(blocking(cp, "T4"))

    def test_blocking_named_cases(self):
        """Named blocking cases from the contract."""
        self.assertFalse(blocking("C5", "T3"))
        self.assertTrue(blocking("C2", "T3"))
        self.assertTrue(blocking("C5", "T4"))
        self.assertFalse(blocking("C5", "T1"))
        self.assertTrue(blocking("C1", ""))


class TestMayApprove(unittest.TestCase):
    """Test the may_approve() function."""

    def test_empty_tier_denied(self):
        """Empty tier → deny with "tier not selected"."""
        allowed, reason = may_approve("C1", "", "agent:liaison/haiku", "user:user1")
        self.assertFalse(allowed)
        self.assertEqual(reason, "tier not selected")

    def test_helper_approver_always_denied(self):
        """Helper approver → deny with "helpers cannot approve"."""
        allowed, reason = may_approve("C1", "T1", "agent:liaison/haiku", "helper:helper1")
        self.assertFalse(allowed)
        self.assertEqual(reason, "helpers cannot approve")

    def test_self_approval_denied(self):
        """Self-approval → deny with "no self-approval"."""
        allowed, reason = may_approve("C1", "T1", "agent:orchestrator/opus", "agent:orchestrator/opus")
        self.assertFalse(allowed)
        self.assertEqual(reason, "no self-approval")

    def test_not_required_allowed(self):
        """Non-required checkpoint → allow with "not required at this tier"."""
        allowed, reason = may_approve("C5", "T1", "agent:haiku-dev/haiku", "user:user1")
        self.assertTrue(allowed)
        self.assertEqual(reason, "not required at this tier")

    def test_user_approval_allowed(self):
        """User approver → allow with "user approval"."""
        allowed, reason = may_approve("C1", "T1", "agent:liaison/haiku", "user:user1")
        self.assertTrue(allowed)
        self.assertEqual(reason, "user approval")

    def test_orchestrator_approving_own_spec_denied(self):
        """Orchestrator approving its own spec → denied."""
        # C2 is spec, required at T1
        allowed, reason = may_approve("C2", "T1", "agent:orchestrator/opus", "agent:orchestrator/opus")
        self.assertFalse(allowed)

    def test_orchestrator_approving_haiku_plan_at_t2(self):
        """Orchestrator approving haiku plan at T2 → allowed."""
        # C5 is plan, required at T2, orchestrator can approve C5 at T2
        allowed, reason = may_approve("C5", "T2", "agent:haiku-dev/haiku", "agent:orchestrator/opus")
        self.assertTrue(allowed)

    def test_orchestrator_approving_at_t3_denied(self):
        """Orchestrator cannot approve anything at T3."""
        for cp in ["C1", "C5", "C6"]:
            allowed, reason = may_approve(cp, "T3", "agent:haiku-dev/haiku", "agent:orchestrator/opus")
            self.assertFalse(allowed)
            self.assertIn("orchestrator may not approve", reason)

    def test_orchestrator_approving_at_t4_denied(self):
        """Orchestrator cannot approve anything at T4."""
        allowed, reason = may_approve("C5", "T4", "agent:haiku-dev/haiku", "agent:orchestrator/opus")
        self.assertFalse(allowed)
        self.assertIn("orchestrator may not approve", reason)

    def test_orchestrator_needs_agent_author(self):
        """Orchestrator approval needs agent author."""
        # Human author at T1, C1 is in ORCH_OK but author is human
        allowed, reason = may_approve("C1", "T1", "user:user1", "agent:orchestrator/opus")
        self.assertFalse(allowed)
        self.assertEqual(reason, "human-authored work needs a user")

    def test_author_outranks_approver(self):
        """Author outranking orchestrator approver → denied."""
        # Sonnet author, haiku orchestrator approver
        # At T2, C5 is in ORCH_OK, so we get past that check and fail on model rank
        allowed, reason = may_approve("C5", "T2", "agent:issue-clerk/sonnet", "agent:orchestrator/haiku")
        self.assertFalse(allowed)
        self.assertEqual(reason, "author outranks approver")

    def test_non_orchestrator_agent_denied(self):
        """Non-orchestrator agent approver → denied."""
        allowed, reason = may_approve("C1", "T1", "agent:liaison/haiku", "agent:issue-clerk/sonnet")
        self.assertFalse(allowed)
        self.assertEqual(reason, "approver not authorised")

    def test_orchestrator_approving_c5_at_t1_not_required(self):
        """C5 isn't required at T1, so rule 4 allows it before the ORCH_OK check."""
        allowed, reason = may_approve("C5", "T1", "agent:haiku-dev/haiku", "agent:orchestrator/opus")
        self.assertTrue(allowed)
        self.assertEqual(reason, "not required at this tier")

    def test_orchestrator_approving_c6_at_t2(self):
        """Orchestrator can approve C6 at T2."""
        allowed, reason = may_approve("C6", "T2", "agent:haiku-dev/haiku", "agent:orchestrator/opus")
        self.assertTrue(allowed)

    def test_helper_always_denied(self):
        """A helper approver is denied for every checkpoint, tier and author."""
        for tier in TIERS:
            for cp in CHECKPOINTS:
                for author in AUTHORS:
                    with self.subTest(tier=tier, cp=cp, author=author):
                        allowed, reason = may_approve(cp, tier, author, "helper:helper1")
                        self.assertFalse(allowed)
                        if tier == "":
                            self.assertEqual(reason, "tier not selected")
                        else:
                            self.assertEqual(reason, "helpers cannot approve")

    def test_c3_at_t1_required_and_only_user_may_approve(self):
        """C3 at T1 → required, and only a User may approve it."""
        self.assertTrue(required("C3", "T1"))
        for approver in APPROVERS:
            for author in AUTHORS:
                if approver == author:
                    continue
                with self.subTest(approver=approver, author=author):
                    allowed, reason = may_approve("C3", "T1", author, approver)
                    approver_kind = approver.split(":", 1)[0]
                    if approver_kind == "user":
                        self.assertTrue(allowed)
                    else:
                        self.assertFalse(allowed)


class TestApproverNeeded(unittest.TestCase):
    """Test the approver_needed() function."""

    def test_not_required_returns_none(self):
        """Non-required checkpoint → "none"."""
        result = approver_needed("C5", "T1", "agent:haiku-dev/haiku")
        self.assertEqual(result, "none")

    def test_empty_tier_returns_user(self):
        """Empty tier → "user"."""
        result = approver_needed("C1", "", "agent:liaison/haiku")
        self.assertEqual(result, "user")

    def test_orchestrator_can_approve_returns_orchestrator(self):
        """Orchestrator can approve → "orchestrator"."""
        result = approver_needed("C5", "T2", "agent:haiku-dev/haiku")
        self.assertEqual(result, "orchestrator")

    def test_orchestrator_cannot_approve_returns_user(self):
        """Orchestrator cannot approve → "user"."""
        result = approver_needed("C5", "T3", "agent:haiku-dev/haiku")
        self.assertEqual(result, "user")

    def test_human_authored_returns_user(self):
        """Human-authored work → "user"."""
        result = approver_needed("C1", "T1", "user:user1")
        self.assertEqual(result, "user")

    def test_t1_c7_by_agent_returns_orchestrator(self):
        """C7 at T1 by agent → orchestrator can approve."""
        result = approver_needed("C7", "T1", "agent:haiku-dev/haiku")
        self.assertEqual(result, "orchestrator")


class TestCrossProduct(unittest.TestCase):
    """
    Full cross-product loop: tiers x checkpoints x authors x approvers,
    checked against expected-value functions written independently of the
    implementation's if-chain.
    """

    def test_required_cross_product(self):
        for tier in TIERS:
            for cp in CHECKPOINTS:
                with self.subTest(tier=tier, cp=cp):
                    self.assertEqual(required(cp, tier), expected_required(cp, tier))

    def test_blocking_cross_product(self):
        for tier in TIERS:
            for cp in CHECKPOINTS:
                with self.subTest(tier=tier, cp=cp):
                    self.assertEqual(blocking(cp, tier), expected_blocking(cp, tier))

    def test_may_approve_cross_product(self):
        for tier in TIERS:
            for cp in CHECKPOINTS:
                for author in AUTHORS:
                    for approver in APPROVERS:
                        with self.subTest(tier=tier, cp=cp, author=author, approver=approver):
                            allowed, reason = may_approve(cp, tier, author, approver)
                            exp_allowed, exp_reason = expected_may_approve(cp, tier, author, approver)
                            self.assertEqual(allowed, exp_allowed)
                            self.assertEqual(reason, exp_reason)

    def test_approver_needed_cross_product(self):
        for tier in TIERS:
            for cp in CHECKPOINTS:
                for author in AUTHORS:
                    with self.subTest(tier=tier, cp=cp, author=author):
                        self.assertEqual(
                            approver_needed(cp, tier, author),
                            expected_approver_needed(cp, tier, author),
                        )


if __name__ == "__main__":
    unittest.main()
