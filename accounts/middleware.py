from django.http import JsonResponse
from .models import UserSession

class SessionValidationMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        session_id = request.headers.get('X-Session-Id')
        
        if session_id:
            session = UserSession.objects.filter(
                session_id=session_id,
                is_active=True
            ).first()

            if not session:
                return JsonResponse(
                    {"status": "error", "message": "Session expired. Please login again."},
                    status=401
                )

        return self.get_response(request)