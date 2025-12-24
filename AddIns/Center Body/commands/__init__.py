# Here you define the commands that will be added to your add-in.

from .commandDialog import entry as commandDialog

# List of command modules - Fusion will automatically call start() and stop()
commands = [
    commandDialog,
]


def start():
    """Called when the add-in starts."""
    for command in commands:
        command.start()


def stop():
    """Called when the add-in stops."""
    for command in commands:
        command.stop()

#gittest