# plans/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import PlanViewSet, UserPlanViewSet

router = DefaultRouter()
router.register(r'', PlanViewSet, basename='plans')

# UserPlan router
user_plan_router = DefaultRouter()
user_plan_router.register(r'user-plan', UserPlanViewSet, basename='user-plan')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(user_plan_router.urls)),
]