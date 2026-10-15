"""Shared slowapi Limiter instance so main.py and routers reference the
same limiter (required for slowapi's per-route @limiter.limit() decorator
to work correctly with the exception handler registered on the app)."""
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
