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
    """
    Accepts multipart/form-data:
      - audioFile: the Blob/webm
      - language: e.g. "en-IN"
    Returns JSON { transcribedText: str }
    """
    audio = request.FILES.get("audioFile")
    lang  = request.POST.get("language", "")
    if not audio or not lang:
        return Response({"detail": "audioFile + language required"},
                        status=status.HTTP_400_BAD_REQUEST)

    # write to temp file
    ext = audio.name.split(".")[-1]
    tf = tempfile.NamedTemporaryFile(delete=False, suffix=f".{ext}")
    for chunk in audio.chunks():
        tf.write(chunk)
    tf.flush()
    tf.close()

    try:
        # whisper expects ISO code like "en"
        code = lang.split("-")[0]
        result = _whisper_model.transcribe(tf.name, language=code)
        text = result.get("text", "").strip()
    finally:
        os.unlink(tf.name)

    return Response({"transcribedText": text})