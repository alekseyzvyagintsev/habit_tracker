###################################################################################
from rest_framework import serializers

from tracker.models import Habit


class HabitSerializer(serializers.ModelSerializer):
    """
    Сериализатор для модели Habit.
    Включает все поля, поле 'id' — только для чтения.
    """

    class Meta:
        model = Habit
        fields = "__all__"
        read_only_fields = ("id",)


###################################################################################
