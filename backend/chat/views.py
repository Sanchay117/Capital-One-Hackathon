from agriadvisor.utils import generate_answer, get_gemini_response
from django.contrib.auth.models import User
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import ChatMessage
from .serializers import RegisterSerializer, ChatMessageSerializer
from rest_framework.views import APIView
from rest_framework.decorators import api_view, permission_classes  # add decorator imports

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(TokenObtainPairView):
    permission_classes = [permissions.AllowAny]

class ChatMessageViewSet(viewsets.ModelViewSet):
    serializer_class = ChatMessageSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return ChatMessage.objects.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        user_text = request.data.get('text', '').strip()
        if not user_text:
            return Response({"detail":"Empty message"}, status=status.HTTP_400_BAD_REQUEST)

        user_msg = ChatMessage.objects.create(
            user=request.user, sender='user', text=user_text
        )
        ai_text = generate_answer(user_text)
        ai_msg = ChatMessage.objects.create(
            user=request.user, sender='ai', text=ai_text
        )

        data = ChatMessageSerializer([user_msg, ai_msg], many=True).data
        return Response(data, status=status.HTTP_201_CREATED)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def prompt_view(request):
    prompt_text = request.data.get('prompt', '').strip()
    if not prompt_text:
        return Response({'detail': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
    answer = generate_answer(prompt_text)
    return Response({'answer': answer}, status=status.HTTP_200_OK)

class PromptAPIView(APIView):
    """
    Handles AI prompt requests.
    Receives a text prompt and returns a response from the Gemini model.
    """
    permission_classes = [permissions.AllowAny] # TODO: Change to [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        prompt = request.data.get("prompt")
        language = request.data.get("language", "en") # Default to English

        if not prompt:
            return Response(
                {"error": "Prompt not provided"},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # TODO: Once authentication is added, save messages to the database
            # ChatMessage.objects.create(user=request.user, sender='user', text=prompt)

            # Get response from the LLM
            ai_response = get_gemini_response(prompt, language)

            # TODO: Once authentication is added, save AI response to the database
            # ChatMessage.objects.create(user=request.user, sender='ai', text=ai_response)

            return Response({"response": ai_response}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"error": f"Error processing prompt: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )