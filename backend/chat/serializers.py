from django.contrib.auth.models import User
from rest_framework import serializers
from .models import ChatMessage

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    class Meta:
        model = User
        fields = ('username', 'password')
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)

class ChatMessageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChatMessage
        fields = ('id', 'sender', 'text', 'created_at')