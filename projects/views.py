# projects/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Project
from .serializers import ProjectSerializer
 

class ProjectListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # optional filter: ?type=draft or ?type=completed
        filter_type = request.query_params.get("type")

        projects = Project.objects.filter(user=request.user).order_by("-created_at")

        if filter_type == "draft":
            projects = projects.filter(is_draft=True)
        elif filter_type == "completed":
            projects = projects.filter(is_draft=False)

        serializer = ProjectSerializer(projects, many=True)
        return Response({"status": "success", "projects": serializer.data})
    
    def post(self, request):
        serializer = ProjectSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response({"status": "success", "project": serializer.data})
        return Response({"status": "error", "errors": serializer.errors}, status=400)



class ProjectDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            project = Project.objects.get(id=pk, user=request.user)
            serializer = ProjectSerializer(project)
            return Response({"status": "success", "project": serializer.data})
        except Project.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=404)

    def put(self, request, pk):
        try:
            project = Project.objects.get(id=pk, user=request.user)
            serializer = ProjectSerializer(project, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"status": "success", "project": serializer.data})

            return Response(
                {"status": "error", "errors": serializer.errors}, status=400
            )

        except Project.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=404)

    def delete(self, request, pk):
        try:
            project = Project.objects.get(id=pk, user=request.user)
            project.delete()
            return Response({"status": "success", "message": "Deleted"})
        except Project.DoesNotExist:
            return Response({"status": "error", "message": "Not found"}, status=404)

class ProjectStatsView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        t1_total = Project.objects.filter(project_type="t1", is_draft=False).count()  # ← add is_draft=False
        t2_total = Project.objects.filter(project_type="t2", is_draft=False).count()  # ← add is_draft=False

        return Response({
            "status": "success",
            "total_projects": t1_total + t2_total,
            "t1_projects": t1_total,
            "t2_projects": t2_total,
        })
