from uuid import UUID

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.db_models import Exercise, User, Workout, WorkoutLog
from app.models.workout import WorkoutCreate, WorkoutLogCreate, WorkoutLogResponse, WorkoutResponse


class WorkoutService:
    def to_workout_response(self, workout: Workout) -> WorkoutResponse:
        return WorkoutResponse(
            id=str(workout.id),
            user_id=str(workout.user_id),
            name=workout.name,
            workout_type=workout.workout_type,
            created_at=workout.created_at,
        )

    def to_log_response(self, log: WorkoutLog) -> WorkoutLogResponse:
        return WorkoutLogResponse(
            id=str(log.id),
            user_id=str(log.user_id),
            exercise_id=str(log.exercise_id),
            workout_id=str(log.workout_id),
            sets=log.sets,
            reps=log.reps,
            weight_kg=log.weight_kg,
            logged_at=log.logged_at,
        )

    async def create_workout(
        self,
        db: AsyncSession,
        user: User,
        payload: WorkoutCreate,
    ) -> WorkoutResponse:
        workout = Workout(
            user_id=user.id,
            name=payload.name,
            workout_type=payload.workout_type,
        )
        db.add(workout)
        await db.commit()
        await db.refresh(workout)
        return self.to_workout_response(workout)

    async def list_workouts(
        self,
        db: AsyncSession,
        user: User,
    ) -> list[WorkoutResponse]:
        result = await db.execute(
            select(Workout)
            .where(Workout.user_id == user.id)
            .order_by(Workout.created_at.desc())
        )
        workouts = result.scalars().all()
        return [self.to_workout_response(workout) for workout in workouts]

    async def get_user_workout(
        self,
        db: AsyncSession,
        user: User,
        workout_id: UUID,
    ) -> Workout:
        result = await db.execute(
            select(Workout).where(
                Workout.id == workout_id,
                Workout.user_id == user.id,
            )
        )
        workout = result.scalar_one_or_none()
        if workout is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Workout not found",
            )
        return workout

    async def log_set(
        self,
        db: AsyncSession,
        user: User,
        workout_id: UUID,
        payload: WorkoutLogCreate,
    ) -> WorkoutLogResponse:
        workout = await self.get_user_workout(db, user, workout_id)

        exercise_result = await db.execute(
            select(Exercise).where(Exercise.id == payload.exercise_id)
        )
        if exercise_result.scalar_one_or_none() is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Exercise not found",
            )

        log = WorkoutLog(
            user_id=user.id,
            exercise_id=payload.exercise_id,
            workout_id=workout.id,
            sets=payload.sets,
            reps=payload.reps,
            weight_kg=payload.weight_kg,
        )
        db.add(log)
        await db.commit()
        await db.refresh(log)
        return self.to_log_response(log)

    async def list_logs(
        self,
        db: AsyncSession,
        user: User,
        workout_id: UUID,
    ) -> list[WorkoutLogResponse]:
        await self.get_user_workout(db, user, workout_id)
        result = await db.execute(
            select(WorkoutLog)
            .where(
                WorkoutLog.workout_id == workout_id,
                WorkoutLog.user_id == user.id,
            )
            .order_by(WorkoutLog.logged_at)
        )
        logs = result.scalars().all()
        return [self.to_log_response(log) for log in logs]
