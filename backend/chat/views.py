from agriadvisor.utils import generate_answer
from django.contrib.auth.models import User
from rest_framework import generics, permissions, viewsets, status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from .models import ChatMessage
from .serializers import RegisterSerializer, ChatMessageSerializer
from main import generate_answer
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
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        prompt = request.data.get('prompt', '').strip()
        if not prompt:
            return Response({'detail': 'Prompt is required.'}, status=status.HTTP_400_BAD_REQUEST)
        answer = generate_answer(prompt)
        return Response({'answer': answer}, status=status.HTTP_200_OK)