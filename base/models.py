from django.db import models
from django.contrib.auth.models import User
# Create your models here.

# models.py - Add these models
from django.contrib.auth.models import User
from django.db import models
import uuid

class AIChatSession(models.Model):
    """Tracks AI chat sessions for each user"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_sessions')
    session_id = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=200, default="AI Assistant Chat")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        return f"{self.user.username}'s Chat: {self.title}"

class AIMessage(models.Model):
    """Stores messages in AI chat sessions"""
    session = models.ForeignKey(AIChatSession, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=20, choices=[
        ('user', 'User'),
        ('assistant', 'AI Assistant'),
        ('system', 'System')
    ])
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    # Store metadata for AI responses
    tokens_used = models.IntegerField(default=0)
    ai_model = models.CharField(max_length=50, null=True, blank=True)
    response_time = models.FloatField(default=0.0)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."

class AIRecommendation(models.Model):
    """Stores AI-generated recommendations based on tasks"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_recommendations')
    task = models.ForeignKey('Task', on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_recommendations')
    recommendation_type = models.CharField(max_length=50, choices=[
        ('break', 'Break Activity'),
        ('related', 'Related Activity'),
        ('productivity', 'Productivity Tip'),
        ('learning', 'Learning Suggestion'),
        ('motivation', 'Motivation')
    ])
    content = models.TextField()
    is_completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    ai_model = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.recommendation_type}"


class Task(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    complete = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        order_with_respect_to = 'user'
