from django.db import models
from django.contrib.auth.models import User


class SavedCode(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="saved_codes"
    )

    title = models.CharField(max_length=200)

    # single / compare
    code_type = models.CharField(
        max_length=20,
        default="single"
    )

    # Code A / Single code
    language = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    code = models.TextField(
        blank=True,
        default=""
    )

    # Code B
    language_b = models.CharField(
        max_length=50,
        blank=True,
        default=""
    )

    code_b = models.TextField(
        blank=True,
        default=""
    )

    created_at = models.DateTimeField(auto_now_add=True)

    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.code_type}"