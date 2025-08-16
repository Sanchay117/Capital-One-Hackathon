import uuid
from django.db import models
from django.conf import settings 
from django.contrib.auth.models import AbstractUser

# This CustomUser model STAYS in this file.
class CustomUser(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    google_id = models.CharField(max_length=255, null=True, blank=True, unique=True)
    preferred_language = models.CharField(max_length=10, default='en')
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    def __str__(self):
        return self.email

class Chat(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # THE FIX: Instead of referencing the class directly, we use a string
    # from the settings file. Django knows how to resolve this without circular imports.
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='chats')
    
    title = models.CharField(max_length=100, default='New Chat')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        ordering = ['-updated_at']
    def __str__(self):
        return f"{self.title} by {self.user.email}"

class ChatMessage(models.Model):
    class InputType(models.TextChoices):
        TEXT = 'text', 'Text'
        AUDIO = 'audio', 'Audio'
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    chat = models.ForeignKey(Chat, on_delete=models.CASCADE, related_name='messages')
    prompt_text = models.TextField(default='') 
    response_text = models.TextField(default='')
    input_type = models.CharField(max_length=5, choices=InputType.choices, default=InputType.TEXT)
    input_language = models.CharField(max_length=10, default='en')
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ['created_at']
    def __str__(self):
        return f"Message in chat at {self.created_at}"