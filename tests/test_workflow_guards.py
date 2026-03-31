import unittest

from backend.routes.admin import _would_remove_last_active_admin
from backend.routes.tickets import _is_assignable_support_user, _next_resolved_at


class AdminGuardTests(unittest.TestCase):
    def test_blocks_demoting_last_active_admin(self):
        user = {"role": "admin", "is_active": True}

        self.assertTrue(_would_remove_last_active_admin(user, "agent", 1))

    def test_allows_demoting_inactive_admin(self):
        user = {"role": "admin", "is_active": False}

        self.assertFalse(_would_remove_last_active_admin(user, "agent", 1))


class TicketAssignmentGuardTests(unittest.TestCase):
    def test_accepts_active_support_user(self):
        agent = {"role": "agent", "is_active": True}

        self.assertTrue(_is_assignable_support_user(agent))

    def test_rejects_inactive_support_user(self):
        agent = {"role": "agent", "is_active": False}

        self.assertFalse(_is_assignable_support_user(agent))

    def test_rejects_non_support_role(self):
        requester = {"role": "user", "is_active": True}

        self.assertFalse(_is_assignable_support_user(requester))


class TicketCloseStatusTests(unittest.TestCase):
    def test_close_sets_completion_timestamp_when_missing(self):
        now = object()

        self.assertIs(_next_resolved_at(None, "closed", now), now)

    def test_close_preserves_existing_resolved_timestamp(self):
        resolved_at = "2026-03-31T13:11:56.032000"

        self.assertEqual(_next_resolved_at(resolved_at, "closed", object()), resolved_at)

    def test_reopen_clears_resolved_timestamp(self):
        self.assertIsNone(_next_resolved_at("2026-03-31T13:11:56.032000", "open", object()))


if __name__ == "__main__":
    unittest.main()
