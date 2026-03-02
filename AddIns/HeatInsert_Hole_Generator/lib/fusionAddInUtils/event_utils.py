# lib/fusionAddInUtils/event_utils.py
# Event handling utilities for Fusion 360 add-ins

import adsk.core
import adsk.fusion
import traceback

# Global list to keep handler references alive
_handlers = []


def add_handler(event, handler):
    """Add an event handler and keep a reference to prevent garbage collection."""
    event.add(handler)
    _handlers.append(handler)


def clear_handlers():
    """Clear the handlers list."""
    global _handlers
    _handlers = []
