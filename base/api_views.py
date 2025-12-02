import os
import json
import pandas as pd
from django.contrib.auth.models import User
from django.shortcuts import get_object_or_404
from rest_framework import viewsets, permissions, status, parsers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser


from .models import Task
from .serializers import TaskSerializer

# Try importing UserSerializer, otherwise define a basic one to prevent NameError
try:
    from .serializers import UserSerializer
except ImportError:
    from rest_framework import serializers
    class UserSerializer(serializers.ModelSerializer):
        class Meta:
            model = User
            fields = ['id', 'username', 'email']

# OpenAI Import with Error Handling
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = (MultiPartParser, FormParser, JSONParser)

    def get_queryset(self):
        """Ensure users only see their own tasks."""
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        """Auto-assign the task to the current user."""
        serializer.save(user=self.request.user)

    @action(detail=False, methods=['post'], url_path='upload-bulk')
    def upload_bulk(self, request):
        """
        Import CSV or JSON files.
        """
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            tasks_to_create = []
            
            # Handle CSV
            if file_obj.name.endswith('.csv'):
                df = pd.read_csv(file_obj)
                df = df.fillna('') # Handle empty cells
                for _, row in df.iterrows():
                    tasks_to_create.append(Task(
                        user=request.user,
                        title=row.get('title', 'Untitled CSV Task'),
                        description=row.get('description', ''),
                        complete=bool(row.get('complete', False)) 
                    ))

            # Handle JSON
            elif file_obj.name.endswith('.json'):
                data = json.load(file_obj)
                if isinstance(data, dict): 
                    data = [data]
                
                for item in data:
                    tasks_to_create.append(Task(
                        user=request.user,
                        title=item.get('title', 'Untitled JSON Task'),
                        description=item.get('description', ''),
                        complete=bool(item.get('complete', False))
                    ))
            else:
                return Response({"error": "Unsupported file format. Use CSV or JSON."}, status=status.HTTP_400_BAD_REQUEST)

            Task.objects.bulk_create(tasks_to_create)
            return Response({"message": f"Successfully created {len(tasks_to_create)} tasks."}, status=status.HTTP_201_CREATED)

        except Exception as e:
            return Response({"error": f"Failed to process file: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['post'], url_path='ai-suggest')
    def ai_suggest(self, request):
        """
        Suggests a task description using OpenAI (or Mock data).
        """
        title = request.data.get('title')
        if not title:
            return Response({"error": "Title is required"}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv('OPENAI_API_KEY')
        suggestion = None

        # Real AI
        if api_key and OpenAI:
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are a helpful productivity assistant."},
                        {"role": "user", "content": f"Suggest a short description for: {title}"}
                    ]
                )
                suggestion = response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI Error: {e}")

        # Mock Fallback
        if not suggestion:
            suggestion = f"Mock suggestion for '{title}': Break this into steps and start now."

        return Response({"title": title, "suggestion": suggestion})

    @action(detail=False, methods=['post', 'get'], url_path='ask-madala')
    def ask_madala(self, request):
        """
        'Madala' suggests fun activities in a city.
        """
        city = request.data.get('city') or request.query_params.get('city')
        if not city:
            return Response({"error": "City is required"}, status=status.HTTP_400_BAD_REQUEST)

        api_key = os.getenv('OPENAI_API_KEY')
        advice = None

        if api_key and OpenAI:
            try:
                client = OpenAI(api_key=api_key)
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[
                        {"role": "system", "content": "You are 'Madala', a wise, fun, elderly local guide."},
                        {"role": "user", "content": f"Give me 3 fun, low-cost things to do in {city}."}
                    ]
                )
                advice = response.choices[0].message.content
            except Exception as e:
                print(f"OpenAI Error: {e}")

        if not advice:
            advice = f"Madala says: You are in {city}? Go for a walk, find coffee, and smile!"

        return Response({"city": city, "madala_says": advice})

    @action(detail=False, methods=['get'])
    def analytics(self, request):
        """
        Returns task completion stats.
        """
        qs = self.get_queryset()
        total = qs.count()
        completed = qs.filter(complete=True).count()
        pending = total - completed
        
        return Response({
            "total_tasks": total,
            "completed_tasks": completed,
            "pending_tasks": pending,
            "completion_rate": f"{(completed/total)*100:.1f}%" if total > 0 else "0%"
        })

class UserViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Users. Defined here to avoid circular imports.
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['post', 'delete'], url_path='delete-account')
    def delete_account(self, request):
        """
        Soft delete the user account.
        """
        user = request.user
        user.is_active = False
        user.save()
        return Response({"message": "Account deactivated successfully."}, status=status.HTTP_200_OK)