"""Compatibility re-export for the JWT auth decorators used by the app."""

from backend.middleware.auth_guard import admin_required, agent_required, login_required

__all__ = ["admin_required", "agent_required", "login_required"]
