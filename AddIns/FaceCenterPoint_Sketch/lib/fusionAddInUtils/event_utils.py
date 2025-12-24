"""
Event Utilities for Fusion 360 Add-Ins
Helper functions for managing event handlers.
"""

import adsk.core
import traceback


def add_handler(event, callback_class, handlers_list: list):
    """
    Helper function to add an event handler and keep it alive.
    
    Args:
        event: The event to attach the handler to
        callback_class: The handler class to instantiate
        handlers_list: A list to store the handler reference (prevents garbage collection)
    
    Returns:
        The handler instance
    """
    handler = callback_class()
    event.add(handler)
    handlers_list.append(handler)
    return handler
