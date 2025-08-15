from django.conf import settings
from django.db import models
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
import tempfile, os
import whisper

class ChatMessage(models.Model):
    SENDER_CHOICES = [
        ('user', 'User'),
        ('ai', 'AI'),
    ]
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.CharField(max_length=4, choices=SENDER_CHOICES)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']

# load once at import‐time
_whisper_model = whisper.load_model("base")

@api_view(["POST"])
@permission_classes([AllowAny])
def transcribe_audio(request):
    if 'audio' not in request.FILES:
        return Response({'error': 'No audio file provided'}, status=status.HTTP_400_BAD_REQUEST)

    audio_file = request.FILES['audio']

    with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
        for chunk in audio_file.chunks():
            tmp.write(chunk)
        tmp_path = tmp.name

    try:
        result = _whisper_model.transcribe(tmp_path, fp16=False)
        text = result.get("text", "").strip()
        return Response({'text': text})
    except Exception as e:
        return Response({'error': f"Error during transcription: {e}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)