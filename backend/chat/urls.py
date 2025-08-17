from django.urls import path
from .views import (
    RegisterView,
    GoogleLoginView,
    ChatListView,
    ChatDetailView,
    MessageCreateView,
    TranscribeAudioView,
    UserProfileUpdateView
    )
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
urlpatterns = [
# --- Authentication Endpoints ---
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('login/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('login/google/', GoogleLoginView.as_view(), name='google-login'),
    
    # --- Chat History & Management Endpoints ---
    path('chats/', ChatListView.as_view(), name='chat-list'),
    path('chats/<uuid:pk>/', ChatDetailView.as_view(), name='chat-detail'),

    # --- Message & Agent Interaction Endpoint ---
    path('messages/', MessageCreateView.as_view(), name='create-message'),

    # --- Audio Transcription Endpoint ---
    # THE FIX: Corrected .as_Vew() to .as_view()
    path('transcribe/', TranscribeAudioView.as_view(), name='transcribe-audio'),

    path('profile/language/', UserProfileUpdateView.as_view(), name='update-language'),

]
