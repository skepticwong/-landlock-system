# backend/utils/plot_protection.py
"""
Protection rules for state-held plots (government / military / city).

A plot is "protected" when plot_type is one of the PROTECTED_PLOT_TYPES
(or is_protected is set). Protected plots:
- cannot be edited, sold, listed, leased or transferred by anyone
  (including the recorded owner, chiefs, witnesses, buyers);
- can only be created, updated or re-typed by land officials / superusers;
- are excluded from the sale flow, marketplace and approval chains.
"""

PROTECTED_PLOT_TYPES = {"government", "military", "city"}


def is_state_plot_type(plot_type) -> bool:
    return (plot_type or "").strip().lower() in PROTECTED_PLOT_TYPES


def is_plot_protected(plot) -> bool:
    """Check a plot dict/row for protected status."""
    if not plot:
        return False
    if bool(plot.get("is_protected")):
        return True
    return is_state_plot_type(plot.get("plot_type"))


def locked_response():
    return {
        "error": "This is a state-held plot (government/military/city land). "
                 "It cannot be modified, sold or transferred."
    }, 403
