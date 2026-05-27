from app.models.workout import (
    WorkoutExercise,
    WorkoutGenerateRequest,
    WorkoutResponse,
)


class WorkoutService:
    def generate_workout(self, request: WorkoutGenerateRequest) -> WorkoutResponse:
        return WorkoutResponse(
            name=f"{request.goal.title()} Day (Stub)",
            description=(
                f"Stub workout for {request.experience_level} "
                f"({request.days_per_week} days/week). "
                "Replace with Azure OpenAI + RAG generation."
            ),
            exercises=[
                WorkoutExercise(
                    exercise_id="squat",
                    name="Barbell Back Squat",
                    sets=3,
                    reps="8-10",
                ),
                WorkoutExercise(
                    exercise_id="bench-press",
                    name="Barbell Bench Press",
                    sets=3,
                    reps="8-10",
                ),
                WorkoutExercise(
                    exercise_id="deadlift",
                    name="Conventional Deadlift",
                    sets=3,
                    reps="5",
                ),
            ],
        )
