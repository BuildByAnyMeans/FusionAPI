# config.py
# Configuration and preset data for Heat Insert Hole Generator

import os

# Add-in identity
ADDIN_NAME = 'Heat Insert Hole Generator'
COMPANY_NAME = 'Parker'

# Debug mode
DEBUG = False

# Resource paths
ADDIN_PATH = os.path.dirname(os.path.realpath(__file__))
ICON_PATH = os.path.join(ADDIN_PATH, 'commands', 'commandDialog', 'resources')

# =============================================================================
# HEAT INSERT SPECIFICATIONS
# =============================================================================
# All dimensions in mm
# 
# For each thread size:
#   - options: Available insert lengths with corresponding hole depths
#   - hole_dia: Recommended hole diameter for the insert (top of taper)
#   - entry_dia: Entry diameter for stepped holes
#   - entry_depth: Depth of entry step
#   - od: Outer diameter of insert (reference only)
#   - chamfer_size: Chamfer dimension at 45° (always applied)
#   - melt_relief_oversize: Added to hole_dia for melt relief pocket diameter
#   - melt_relief_depth: Depth of melt relief pocket
# =============================================================================

INSERT_SPECS = {
    'M2': {
        'options': {
            'M2x3 (3.0mm)': {'insert_length': 3.0},
            'M2x4 (4.0mm)': {'insert_length': 4.0},
        },
        'hole_dia': 3.2,
        'entry_dia': 3.6,
        'entry_depth': 0.8,
        'od': 3.5,
        # Chamfer specs (always applied)
        'chamfer_size': 0.35,      # mm at 45°
        # Melt relief specs (optional)
        'melt_relief_oversize': 0.5,   # mm added to hole_dia
        'melt_relief_depth': 0.25,     # mm
    },
    'M2.5': {
        'options': {
            'M2.5x4 (4.0mm)': {'insert_length': 4.0},
            'M2.5x5 (5.0mm)': {'insert_length': 5.0},
        },
        'hole_dia': 3.8,
        'entry_dia': 4.2,
        'entry_depth': 0.8,
        'od': 4.0,
        'chamfer_size': 0.40,
        'melt_relief_oversize': 0.6,
        'melt_relief_depth': 0.30,
    },
    'M3': {
        'options': {
            'M3x4 (4.0mm)': {'insert_length': 4.0},
            'M3x5 (5.0mm)': {'insert_length': 5.0},
            'M3x6 (5.7mm)': {'insert_length': 5.7},
            'M3x8 (8.0mm)': {'insert_length': 8.0},
        },
        'hole_dia': 4.5,
        'entry_dia': 5.0,
        'entry_depth': 1.0,
        'od': 5.0,
        'chamfer_size': 0.50,
        'melt_relief_oversize': 0.7,
        'melt_relief_depth': 0.35,
    },
    'M4': {
        'options': {
            'M4x6 (6.0mm)': {'insert_length': 6.0},
            'M4x8 (8.0mm)': {'insert_length': 8.0},
            'M4x10 (10.0mm)': {'insert_length': 10.0},
        },
        'hole_dia': 5.9,
        'entry_dia': 6.4,
        'entry_depth': 1.0,
        'od': 6.3,
        'chamfer_size': 0.60,
        'melt_relief_oversize': 0.9,
        'melt_relief_depth': 0.45,
    },
    'M5': {
        'options': {
            'M5x8 (8.0mm)': {'insert_length': 8.0},
            'M5x10 (10.0mm)': {'insert_length': 10.0},
            'M5x12 (12.0mm)': {'insert_length': 12.0},
        },
        'hole_dia': 7.1,
        'entry_dia': 7.6,
        'entry_depth': 1.2,
        'od': 7.5,
        'chamfer_size': 0.75,
        'melt_relief_oversize': 1.1,
        'melt_relief_depth': 0.55,
    },
    'M6': {
        'options': {
            'M6x10 (10.0mm)': {'insert_length': 10.0},
            'M6x12 (12.0mm)': {'insert_length': 12.0},
            'M6x14 (14.0mm)': {'insert_length': 14.0},
        },
        'hole_dia': 8.5,
        'entry_dia': 9.0,
        'entry_depth': 1.2,
        'od': 9.0,
        'chamfer_size': 0.90,
        'melt_relief_oversize': 1.3,
        'melt_relief_depth': 0.70,
    }
}

# =============================================================================
# GUARDRAILS / CAPS
# =============================================================================
MAX_MELT_RELIEF_DEPTH = 0.8      # mm - never exceed this
MAX_MELT_RELIEF_OVERSIZE = 1.5   # mm - never exceed this

# =============================================================================
# DEFAULTS
# =============================================================================
BASE_EXTRA_DEPTH = 1.0       # mm - always added to insert length (built-in)
DEFAULT_EXTRA_DEPTH = 0.0    # mm - user-adjustable extra depth (starts at 0)
DEFAULT_TOLERANCE = 0.0      # mm - diameter adjustment
DEFAULT_MELT_RELIEF = True   # Melt relief on by default