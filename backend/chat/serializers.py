from rest_framework import serializers
from .models import CustomUser, Chat, ChatMessage

# Serializer for returning user data (without password)
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ('id', 'username', 'email', 'preferred_language')

# Serializer for the standard registration form
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = CustomUser
        # We need email, username, password, and the new language field
        fields = ('username', 'password', 'email', 'preferred_language')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(
            username=validated_data['username'],
            email=validated_data['email'],
            password=validated_data['password'],
            preferred_language=validated_data.get('preferred_language', 'en')
        )
        return user

# Serializer for a single message turn
class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = '__all__'

# Serializer for the list of chats in the sidebar (only needs title and id)
class ChatListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Chat
        fields = ('id', 'title', 'updated_at')

# Serializer for a single, detailed chat (includes all messages)
class ChatDetailSerializer(serializers.ModelSerializer):
    messages = ChatMessageSerializer(many=True, read_only=True)

    class Meta:
        model = Chat
        fields = ('id', 'user', 'title', 'created_at', 'updated_at', 'messages')