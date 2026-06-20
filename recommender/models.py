from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=10, blank=True, null=True)

    def __str__(self):
        return self.user.get_full_name() or self.user.username


class Prediction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='predictions')
    N = models.FloatField()
    P = models.FloatField()
    K = models.FloatField()
    temperature = models.FloatField()
    humidity = models.FloatField()
    ph = models.FloatField()
    rainfall = models.FloatField()
    predicted_crop = models.CharField(max_length=15)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} -> {self.predicted_crop}"
    

class DiseasePrediction(models.Model):

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='disease_predictions',
        null=True,
        blank=True
    )

    disease_name = models.CharField(max_length=100)

    confidence = models.FloatField()

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):

        return f"{self.disease_name} ({self.confidence}%)"

    @property
    def formatted_disease_name(self):
        name = self.disease_name
        if "___" in name:
            parts = name.split("___")
            crop = parts[0].replace("_", " ").title()
            disease = parts[1].replace("_", " ").strip().title()
            return f"{crop} - {disease}"
        return name.replace("_", " ").title()