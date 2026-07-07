from __future__ import annotations

from .interfaces import ConstitutionManager
from .models import IntelligencePlan, VerificationResult


class ConstitutionManager(ConstitutionManager):
    """Concrete governance manager."""

    def validate(self, plan: IntelligencePlan) -> VerificationResult:
        raise NotImplementedError
