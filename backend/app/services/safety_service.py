from dataclasses import dataclass

from app.models.db_models import MedicalFlags, User

SAFETY_CONSTRAINT_TEXT = (
    "This user has indicated health considerations. "
    "Provide conservative, general fitness programming only. "
    "Keep intensity and volume moderate, and avoid exercises that place excessive "
    "stress on joints, the cardiovascular system, or the spine. "
    "Do not give medical advice or reference any specific health condition. "
    "Recommend the user consult a healthcare professional before starting."
)


@dataclass
class SafetyConstraints:
    requires_consult: bool
    constraint_text: str
    disclaimer: str


def build_safety_constraints(
    user: User,  # noqa: ARG001 — reserved for future user-level flags
    medical_flags: MedicalFlags | None,
) -> SafetyConstraints:
    """
    Returns safety constraint data used to make AI prompts more conservative.

    This is NOT medical diagnosis — it only signals the AI to be conservative
    and to recommend professional consultation.
    """
    from app.constants import CONSENT_TEXT

    if medical_flags is None or medical_flags.none:
        return SafetyConstraints(
            requires_consult=False,
            constraint_text="",
            disclaimer=CONSENT_TEXT,
        )

    active_flags = (
        medical_flags.heart_condition
        or medical_flags.diabetes
        or medical_flags.asthma
        or medical_flags.joint_or_back_issues
        or medical_flags.pregnant
        or medical_flags.other
    )

    return SafetyConstraints(
        requires_consult=active_flags,
        constraint_text=SAFETY_CONSTRAINT_TEXT if active_flags else "",
        disclaimer=CONSENT_TEXT,
    )
