from django.conf import settings
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import UserSerializer, RegisterSerializer, ChatListSerializer, ChatDetailSerializer, UserProfileSerializer
from .models import CustomUser, Chat, ChatMessage
from rest_framework.views import APIView

import os
import tempfile
import whisper
import requests

from deep_translator import GoogleTranslator

from agriadvisor.utils import generate_answer

_whisper_model = whisper.load_model("medium")

class RegisterView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

class GoogleLoginView(generics.GenericAPIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        access_token = request.data.get('access_token')
        if not access_token:
            return Response({'error': 'Google access token not provided.'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user_info_url = 'https://www.googleapis.com/oauth2/v3/userinfo'
            headers = {'Authorization': f'Bearer {access_token}'}
            google_response = requests.get(user_info_url, headers=headers)
            google_response.raise_for_status()  
            idinfo = google_response.json()
            email = idinfo['email']
            google_id = idinfo['sub']

            # Check if user exists, otherwise create a new one
            user, created = CustomUser.objects.get_or_create(
                email=email,
                defaults={
                    'google_id': google_id,
                    'username': idinfo.get('given_name', email.split('@')[0]),
                    'first_name': idinfo.get('given_name', ''),
                    'last_name': idinfo.get('family_name', ''),
                }
            )

            refresh = RefreshToken.for_user(user)
            user_data = UserSerializer(user).data

            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': user_data
            })
        except Exception as e:
            return Response({'error': f'Invalid Google token or failed to fetch user info: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)


class ChatListView(generics.ListAPIView):
    serializer_class = ChatListSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
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

        # 2. Get the answer from RAG agent, with translation
        try:
            prompt_for_model = prompt
            if input_language != 'en':
                prompt_for_model = GoogleTranslator(source=input_language, target='en').translate(prompt)

            english_response = generate_answer(prompt_for_model)

            response_text = english_response
            if input_language != 'en':
                response_text = GoogleTranslator(source='en', target=input_language).translate(english_response)

        except Exception as e:
            print(f"Error during translation or RAG agent call: {e}")
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
        # Get the language from the request, default to 'en' if not provided
        language = request.data.get('language', 'en')
        tmp_path = None 

        # Save the uploaded file to a temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".webm") as tmp:
            for chunk in audio_file.chunks():
                tmp.write(chunk)
            tmp_path = tmp.name

        try:
            result = _whisper_model.transcribe(tmp_path, language=language, fp16=False)
            text = result.get("text", "").strip()            
            detected_language = result.get("language", "en")

            return Response({'text': text, 'language': detected_language})

        except Exception as e:
            print(f"Error during Whisper transcription: {e}")
            return Response({'error': 'Failed to process audio.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        finally:
            # Clean up the temporary file
            if tmp_path and os.path.exists(tmp_path):
                os.remove(tmp_path)

    
class UserProfileUpdateView(generics.UpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user