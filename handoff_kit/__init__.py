"""handoff-kit: agent task handoff records with tamper-evident receipts."""
from .core import create_handoff, validate_handoff, merge_handoff, verify_receipt, canonical, SPEC_VERSION
__all__ = ["create_handoff", "validate_handoff", "merge_handoff", "verify_receipt", "canonical", "SPEC_VERSION"]
