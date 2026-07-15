# plans/views.py


from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated

from django.utils import timezone
from datetime import timedelta

from .models import Plan, UserPlan
from .serializers import PlanSerializer
from accounts.models import Customer
from plans.permissions import IsCustomAdmin



# Plans
#! GET     /plans/
#! POST    /plans/
#! PUT     /plans/{id}/
#! DELETE  /plans/{id}/

# =========================
# PLAN CRUD (Admin controlled)
# =========================

class PlanViewSet(viewsets.ModelViewSet):
    queryset = Plan.objects.all()
    serializer_class = PlanSerializer

    def get_permissions(self):
        # Anyone can list/retrieve plans
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        # Only custom admin can create/update/delete
        return [IsCustomAdmin()]
    
        # Optional: You can add search/filter
        # filter_backends = [DjangoFilterBackend, SearchFilter]
        # search_fields = ['name', 'tool']
# ...............................................................


# User Plans
#! Assign
# POST /plans/user-plan/assign/
#! Remove
# POST /plans/user-plan/remove/
#! Get User Plan
# GET /plans/user-plan/get_user_plan/?user_id=5

# =========================
# USER PLAN MANAGEMENT
# =========================
class UserPlanViewSet(viewsets.ViewSet):
    """
    User Plan Management:
    - assign/remove → admin only
    - get_user_plan → authenticated users (own plan)
    """
    permission_classes = [IsCustomAdmin]  # default

    def get_permissions(self):
        """
        Override permissions per action
        """
        if self.action in ["get_user_plan", "use_tool"]:
            return [IsAuthenticated()]  # normal logged-in users
        return [IsCustomAdmin()]  # assign/remove → admin only
    

    # ASSIGN PLAN
    # =========================
    @action(detail=False, methods=['post'])
    def assign(self, request):
        try:
            user_id = request.data.get("user_id")
            plan_id = request.data.get("plan_id")

            if not user_id or not plan_id:
                return Response(
                    {"success": False, "message": "user_id and plan_id are required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user = Customer.objects.get(id=user_id)
            plan = Plan.objects.get(id=plan_id)
            now = timezone.now()

            user_plan, created = UserPlan.objects.get_or_create(customer=user)

            # =========================
            # START / RENEW LOGIC (UPDATED)
            # =========================
            if created or not user_plan.start_date or user_plan.end_date <= now:
                # Fresh or expired plan → allow
                user_plan.start_date = now
                user_plan.end_date = now + timedelta(days=plan.duration_days)

            else:
                # =========================
                # CHECK IF CURRENT PLAN IS FULLY USED
                # =========================
                current_plan = user_plan.plan
                allow_new_plan = False

                if current_plan:
                    if current_plan.is_unlimited:
                        # Unlimited → never completes
                        allow_new_plan = False

                    elif current_plan.tool == "t1":
                        limit = current_plan.t1_projects_limit or 0
                        allow_new_plan = user_plan.t1_projects_used >= limit

                    elif current_plan.tool == "t2":
                        limit = current_plan.t2_projects_limit or 0
                        allow_new_plan = user_plan.t2_projects_used >= limit

                    elif current_plan.tool == "hybrid":
                        t1_limit = current_plan.t1_projects_limit or 0
                        t2_limit = current_plan.t2_projects_limit or 0

                        allow_new_plan = (
                            user_plan.t1_projects_used >= t1_limit and
                            user_plan.t2_projects_used >= t2_limit
                        )

                if allow_new_plan:
                    user_plan.start_date = now
                    user_plan.end_date = now + timedelta(days=plan.duration_days)
                else:
                    return Response({
                        "success": False,
                        "message": "User already has an active plan"
                    }, status=status.HTTP_400_BAD_REQUEST)

            # =========================
            # ASSIGN PLAN
            # =========================
            user_plan.plan = plan
            user_plan.active = True

            # =========================
            # RESET PROJECT USAGE BASED ON TOOL
            # =========================
            user_plan.t1_projects_used = 0 if plan.tool in ["t1", "hybrid"] else user_plan.t1_projects_used
            user_plan.t2_projects_used = 0 if plan.tool in ["t2", "hybrid"] else user_plan.t2_projects_used

            user_plan.save()

            return Response({
                "success": True,
                "message": "Plan assigned successfully"
            })

        except Customer.DoesNotExist:
            return Response({"success": False, "message": "User not found"}, status=status.HTTP_404_NOT_FOUND)

        except Plan.DoesNotExist:
            return Response({"success": False, "message": "Plan not found"}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)


    # REMOVE PLAN
    # =========================
    @action(detail=False, methods=['post'])
    def remove(self, request):
        try:
            user_id = request.data.get("user_id")

            if not user_id:
                return Response(
                    {"success": False, "message": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            user_plan = UserPlan.objects.get(customer_id=user_id)

            # Deactivate and clear plan
            user_plan.active = False
            user_plan.plan = None
            user_plan.start_date = None
            user_plan.end_date = None

            # Reset usage counters for all tools
            user_plan.t1_projects_used = 0
            user_plan.t2_projects_used = 0

            user_plan.save()

            return Response({
                "success": True,
                "message": "Plan removed successfully"
            })

        except UserPlan.DoesNotExist:
            return Response(
                {"success": False, "message": "No plan found for this user"},
                status=status.HTTP_404_NOT_FOUND
            )

        except Exception as e:
            return Response(
                {"success": False, "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )


    # =========================
    # GET USER PLAN (AUTHENTICATED USER)
    # =========================        
    @action(detail=False, methods=['get'])
    def get_user_plan(self, request):
        try:
            user_id = request.query_params.get("user_id")
            if not user_id:
                return Response(
                    {"success": False, "message": "user_id is required"},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Security check
            if str(request.user.id) != str(user_id) and getattr(request.user, "role", None) != "admin":
                return Response({"detail": "Forbidden"}, status=403)

            user_plan = UserPlan.objects.select_related("plan").get(customer_id=user_id)
            plan = user_plan.plan

            if not plan:
                return Response({
                    "success": True,
                    "data": {
                        "plan_name": None,
                        "tool": None,
                        "active": False,
                        "projects_usage": None,
                        "display": None
                    }
                })

            # =========================
            # BUILD USAGE DATA
            # =========================
            usage_data = {}
            display = None

            if plan.is_unlimited:
                # UNLIMITED
                if plan.tool == "t1":
                    usage_data["t1"] = {
                        "used": user_plan.t1_projects_used,
                        "limit": "∞"
                    }
                    display = f"{user_plan.t1_projects_used}/∞"

                elif plan.tool == "t2":
                    usage_data["t2"] = {
                        "used": user_plan.t2_projects_used,
                        "limit": "∞"
                    }
                    display = f"{user_plan.t2_projects_used}/∞"

                elif plan.tool == "hybrid":
                    usage_data["t1"] = {
                        "used": user_plan.t1_projects_used,
                        "limit": "∞"
                    }
                    usage_data["t2"] = {
                        "used": user_plan.t2_projects_used,
                        "limit": "∞"
                    }
                    display = f"{user_plan.t1_projects_used}/∞, {user_plan.t2_projects_used}/∞"

            else:
                # LIMITED
                if plan.tool == "t1":
                    limit = plan.t1_projects_limit or 0
                    usage_data["t1"] = {
                        "used": user_plan.t1_projects_used,
                        "limit": limit
                    }
                    display = f"{user_plan.t1_projects_used}/{limit}"

                elif plan.tool == "t2":
                    limit = plan.t2_projects_limit or 0
                    usage_data["t2"] = {
                        "used": user_plan.t2_projects_used,
                        "limit": limit
                    }
                    display = f"{user_plan.t2_projects_used}/{limit}"

                elif plan.tool == "hybrid":
                    t1_limit = plan.t1_projects_limit or 0
                    t2_limit = plan.t2_projects_limit or 0

                    usage_data["t1"] = {
                        "used": user_plan.t1_projects_used,
                        "limit": t1_limit
                    }
                    usage_data["t2"] = {
                        "used": user_plan.t2_projects_used,
                        "limit": t2_limit
                    }

                    display = f"{user_plan.t1_projects_used}/{t1_limit}, {user_plan.t2_projects_used}/{t2_limit}"

            # =========================
            # RESPONSE
            # =========================
            return Response({
                "success": True,
                "data": {
                    "plan_name": plan.name,
                    "tool": plan.tool,
                    "start_date": user_plan.start_date,
                    "end_date": user_plan.end_date,
                    "active": user_plan.active,
                    "is_unlimited": plan.is_unlimited,
                    "projects_usage": usage_data,

                    # ✅ NEW (important for frontend)
                    "usage_display": display
                }
            })

        except UserPlan.DoesNotExist:
            return Response({
                "success": False,
                "message": "No plan found"
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


    # =========================
    # USE TOOL (CREATE PROJECT)
    # =========================
    @action(detail=False, methods=['post'])
    def use_tool(self, request):
        try:
            user = request.user
            tool = request.data.get("tool")  # 't1' or 't2'

            if tool not in ["t1", "t2"]:
                return Response({
                    "success": False,
                    "message": "Invalid tool"
                }, status=400)

            # Fetch user's plan
            user_plan = UserPlan.objects.select_related("plan").get(customer=user)
            plan = user_plan.plan

            # =========================
            # CHECK PLAN ACTIVE & EXPIRATION
            # =========================
            if not user_plan.active:
                return Response({
                    "success": False,
                    "message": "No active plan"
                }, status=403)

            if user_plan.end_date and user_plan.end_date < timezone.now():
                user_plan.active = False
                user_plan.save()
                return Response({
                    "success": False,
                    "message": "Plan expired"
                }, status=403)

            # =========================
            # CHECK TOOL ACCESS
            # =========================
            if plan.tool not in [tool, "hybrid"]:
                return Response({
                    "success": False,
                    "message": f"{tool} not allowed in your plan"
                }, status=403)

            # =========================
            # HANDLE UNLIMITED PLAN
            # =========================
            if plan.is_unlimited:
                if tool == "t1":
                    user_plan.t1_projects_used += 1
                else:  # t2
                    user_plan.t2_projects_used += 1

                user_plan.save()
                return Response({
                    "success": True,
                    "message": f"{tool.upper()} project created (unlimited)",
                    "t1_used": user_plan.t1_projects_used,
                    "t2_used": user_plan.t2_projects_used
                })

            # =========================
            # HANDLE LIMITED PLANS
            # =========================
            if tool == "t1":
                limit = plan.t1_projects_limit or 0
                if user_plan.t1_projects_used >= limit:
                    return Response({
                        "success": False,
                        "message": "Limit reached"
                    }, status=403)
                user_plan.t1_projects_used += 1

            elif tool == "t2":
                limit = plan.t2_projects_limit or 0
                if user_plan.t2_projects_used >= limit:
                    return Response({
                        "success": False,
                        "message": "Limit reached"
                    }, status=403)
                user_plan.t2_projects_used += 1

            user_plan.save()

            return Response({
                "success": True,
                "message": f"{tool.upper()} project created",
                "t1_used": user_plan.t1_projects_used,
                "t2_used": user_plan.t2_projects_used,
                "t1_limit": plan.t1_projects_limit,
                "t2_limit": plan.t2_projects_limit
            })

        except UserPlan.DoesNotExist:
            return Response({
                "success": False,
                "message": "No plan found"
            }, status=404)

        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=400)