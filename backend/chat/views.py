from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer, ChatListSerializer, ChatDetailSerializer
from .models import CustomUser, Chat, ChatMessage
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions


from google.cloud import speech
import os

from google.oauth2 import id_token
from google.auth.transport import requests

# from .agent import generate_answer

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class GoogleLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        token = request.data.get('token')
        if not token:
            return Response({'error': 'Google token not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Verify the token with Google's servers
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), settings.GOOGLE_CLIENT_ID)
            email = idinfo['email']
            google_id = idinfo['sub']

            # Check if user exists, otherwise create a new one
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'google_id': google_id,
                    'username': email.split('@')[0] # A default username
                }
            )

            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            })
        except ValueError:
            return Response({'error': 'Invalid Google token.'}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        


class ChatListView(generics.ListAPIView):
    serializer_class = ChatListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return all chats for the current user, most recently updated first
        return Chat.objects.filter(user=self.request.user)
    
class ChatDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = ChatDetailSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Chat.objects.filter(user=self.request.user)
    
class MessageCreateView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        user = request.user
        prompt = request.data.get('prompt')
        chat_id = request.data.get('chat_id')
        input_type = request.data.get('input_type', 'text')
        input_language = request.data.get('input_language', 'en')

        if not prompt:
            return Response({'error': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # 1. Find or Create the Chat Session
        if chat_id:
            try:
                chat = Chat.objects.get(id=chat_id, user=user)
            except Chat.DoesNotExist:
                return Response({'error': 'Chat not found or access denied.'}, status=status.HTTP_404_NOT_FOUND)
        else:
            # Create a new chat and generate a title from the first prompt
            title = ' '.join(prompt.split()[:5])
            if len(prompt.split()) > 5:
                title += '...'
            chat = Chat.objects.create(user=user, title=title)

        # 2. Get the answer from your RAG agent
        try:
            response_text = generate_answer(prompt)
        except Exception as e:
            print(f"Error from RAG agent: {e}")
            response_text = "Sorry, I encountered an error. Please try again."

        # 3. Save the new message to the database
        ChatMessage.objects.create(
            chat=chat,
            prompt_text=prompt,
            response_text=response_text,
            input_type=input_type,
            input_language=input_language
        )

        # 4. Return the complete, updated chat object
        serializer = ChatDetailSerializer(chat)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
@method_decorator(csrf_exempt, name='dispatch')
class TranscribeAudioView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

def post(self, request, *args, **kwargs):
    if 'audio' not in request.FILES:
        return Response({'error': 'No audio file provided.'}, status=status.HTTP_400_BAD_REQUEST)

    audio_file = request.FILES['audio']
    client = speech.SpeechClient()
    audio = speech.RecognitionAudio(content=audio_file.read())

    config = speech.RecognitionConfig(
        encoding=speech.RecognitionConfig.AudioEncoding.WEBM_OPUS,
        sample_rate_hertz=48000,
        language_code="en-US", # A fallback
        alternative_language_codes=["en-IN", "hi-IN", "ta-IN", "te-IN", "kn-IN", "mr-IN", "pa-IN", "bn-IN", "gu-IN", "ur-IN", "ml-IN", "or-IN"],
        enable_automatic_punctuation=True,
    )

    try:
        response = client.recognize(config=config, audio=audio)
        
        if response.results:
            best_alternative = response.results[0].alternatives[0]
            transcription = best_alternative.transcript
            detected_language = response.results[0].language_code
            return Response({'text': transcription, 'language': detected_language})
        else:
            return Response({'text': "Sorry, I couldn't understand that."})

    except Exception as e:
        print(f"Error calling Google Speech API: {e}")
        return Response({'error': 'Failed to process audio.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)