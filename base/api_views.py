from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .models import Task
from .serializers import TaskSerializer
import pandas as pd
import json
import os

class TaskViewSet(viewsets.ModelViewSet):
    serializer_class = TaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # User Isolation: Only return tasks for the logged-in user
        return Task.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

    # 1. REQUIREMENT: Data Processing (Upload JSON/CSV)
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def upload_bulk(self, request):
        file_obj = request.FILES.get('file')
        if not file_obj:
            return Response({"error": "No file provided."}, status=400)

        try:
            if file_obj.name.endswith('.csv'):
                df = pd.read_csv(file_obj)
                tasks_data = df.to_dict(orient='records')
            elif file_obj.name.endswith('.json'):
                tasks_data = json.load(file_obj)
            else:
                return Response({"error": "Unsupported file type"}, status=400)

            count = 0
            for item in tasks_data:
                # Map CSV headers to Model fields
                if item.get('title'):
                    Task.objects.create(
                        user=request.user,
                        title=item.get('title'),
                        description=item.get('description', ''),
                        complete=item.get('complete', False)
                    )
                    count += 1
            return Response({"message": f"Imported {count} tasks successfully."})
        except Exception as e:
            return Response({"error": str(e)}, status=500)

    # 2. REQUIREMENT: AI Integration
    @action(detail=False, methods=['post'])
    def ai_suggest(self, request):
        title = request.data.get('title')
        # MOCK AI Response (Safe for submission without API Key)
        suggestion = (
            f"AI Suggestion for '{title}':\n"
            "1. Plan - Outline the steps.\n"
            "2. Execute - Do the work.\n"
            "3. Review - Check for errors."
        )
        return Response({"task": title, "suggestion": suggestion})

    # 3. BONUS: Analytics
    @action(detail=False, methods=['get'])
    def analytics(self, request):
        tasks = self.get_queryset()
        total = tasks.count()
        completed = tasks.filter(complete=True).count()
        incomplete = tasks.filter(complete=False).count()
        
        return Response({
            "total_tasks": total,
            "completed": completed,
            "incomplete": incomplete,
            "completion_rate": f"{(completed/total)*100:.1f}%" if total > 0 else "0%"
        })