import uuid
from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    # Legacy fields — kept for backward compat; profile table is authoritative for richer data
    training_years: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    goal: Mapped[str] = mapped_column(String(100), nullable=False, default="general")
    # New fields (nullable — filled via onboarding / consent flow)
    sex: Mapped[str | None] = mapped_column(String(10), nullable=True)
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    consent_accepted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    consent_version: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workouts: Mapped[list["Workout"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )
    profile: Mapped["Profile | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    medical_flags: Mapped["MedicalFlags | None"] = relationship(
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    body_metrics: Mapped[list["BodyMetrics"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class Profile(Base):
    __tablename__ = "profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    height_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    primary_goal: Mapped[str | None] = mapped_column(String(30), nullable=True)
    secondary_constraint: Mapped[str | None] = mapped_column(String(255), nullable=True)
    experience_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    lift_competency: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    activity_level: Mapped[str | None] = mapped_column(String(20), nullable=True)
    training_days_per_week: Mapped[int | None] = mapped_column(
        Integer, nullable=True, default=3
    )
    equipment: Mapped[str | None] = mapped_column(
        String(30), nullable=True, default="full_gym"
    )
    injuries_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    goal_targets: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    goal_timeline_weeks: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="profile")


class MedicalFlags(Base):
    __tablename__ = "medical_flags"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    heart_condition: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    diabetes: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    asthma: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    joint_or_back_issues: Mapped[bool] = mapped_column(
        Boolean, nullable=False, default=False
    )
    pregnant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    other: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    other_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    none: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="medical_flags")


class BodyMetrics(Base):
    __tablename__ = "body_metrics"
    __table_args__ = (
        Index("ix_body_metrics_user_recorded", "user_id", "recorded_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    weight_kg: Mapped[float | None] = mapped_column(Float, nullable=True)
    body_fat_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    waist_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    hip_cm: Mapped[float | None] = mapped_column(Float, nullable=True)
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="body_metrics")


class Exercise(Base):
    __tablename__ = "exercises"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    muscle_group: Mapped[str] = mapped_column(String(100), nullable=False)
    equipment: Mapped[str] = mapped_column(String(100), nullable=False)
    difficulty: Mapped[str] = mapped_column(String(50), nullable=False)

    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="exercise", cascade="all, delete-orphan"
    )


class Workout(Base):
    __tablename__ = "workouts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    workout_type: Mapped[str] = mapped_column(String(100), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="workouts")
    workout_logs: Mapped[list["WorkoutLog"]] = relationship(
        back_populates="workout", cascade="all, delete-orphan"
    )


class WorkoutLog(Base):
    __tablename__ = "workout_logs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False
    )
    exercise_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="CASCADE"),
        nullable=False,
    )
    workout_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workouts.id", ondelete="CASCADE"),
        nullable=False,
    )
    sets: Mapped[int] = mapped_column(Integer, nullable=False)
    reps: Mapped[int] = mapped_column(Integer, nullable=False)
    weight_kg: Mapped[float] = mapped_column(Float, nullable=False)
    logged_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    user: Mapped["User"] = relationship(back_populates="workout_logs")
    exercise: Mapped["Exercise"] = relationship(back_populates="workout_logs")
    workout: Mapped["Workout"] = relationship(back_populates="workout_logs")
