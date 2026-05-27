from app.models.exercise import Exercise


class ExerciseService:
    def list_exercises(self) -> list[Exercise]:
        return [
            Exercise(
                id="squat",
                name="Barbell Back Squat",
                muscle_group="legs",
                equipment="barbell",
            ),
            Exercise(
                id="bench-press",
                name="Barbell Bench Press",
                muscle_group="chest",
                equipment="barbell",
            ),
            Exercise(
                id="deadlift",
                name="Conventional Deadlift",
                muscle_group="back",
                equipment="barbell",
            ),
        ]
