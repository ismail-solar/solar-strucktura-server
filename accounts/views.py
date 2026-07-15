# accounts/views.py

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from .models import Customer, UserSession
import json
from django.db import transaction
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.utils.timezone import now
from datetime import timedelta
from plans.models import UserPlan
import random
import uuid
import traceback
# Create your views here.


# * =========================
# * SIGNUP
# * =========================
@csrf_exempt
def signup(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            # ? EXTRACT FIELDS
            name = data.get("name")
            email = data.get("email")
            password = data.get("password")
            address = data.get("address")
            role = data.get("role", "customer").lower()

            # ? VALIDATE FIELDS
            if Customer.objects.filter(email=email).exists():
                return JsonResponse(
                    {"status": "error", "message": "User already exists"}, status=400
                )

            # ? CREATE USER
            user = Customer(
                name=name,
                email=email,
                address=address,
                role=role,
                plain_password=password,
            )

            # ? SET PASSWORD SECURELY (uses hashing)
            user.set_password(password)

            # ? SAVE USER TO DB
            user.save()

            # ? RETURN SUCCESS RESPONSE WITH USER INFO (excluding password)
            return JsonResponse(
                {
                    "status": "success",
                    "message": f"{user.role.capitalize()} created successfully",
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "address": user.address,
                        "role": user.role,
                    },
                }
            )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# * =========================
# * SIGNIN
# * =========================
@csrf_exempt
def signin(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            device_id = data.get("device_id")
            device_name = data.get("device_name", "Unknown Device")
            email = data.get("email")
            password = data.get("password")
            force_logout = data.get("force_logout", False)

            # ? AUTHENTICATE USER
            user = authenticate(request, email=email, password=password)
            if not user:
                return JsonResponse(
                    {"status": "error", "message": "Invalid credentials"},
                    status=401,
                )

            # ? DEACTIVATED CHECK
            if not user.is_active_account:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Your account is deactivated. Please contact admin.",
                    },
                    status=403,
                )

            # ? DEMO LOGIC CHECK
            if user.role == "demo":
                if user.demo_expires_at and user.demo_expires_at < now():
                    user.is_demo_active = False
                    user.save()
                    return JsonResponse(
                        {
                            "status": "error",
                            "message": "Demo expired. Please contact admin.",
                        },
                        status=403,
                    )

            # ? CHECK EXISTING SESSION
            active_session = UserSession.objects.filter(
                user=user, is_active=True
            ).first()

            if active_session and active_session.device_id != device_id:
                if not force_logout:
                    # Tell frontend: already logged in elsewhere
                    return JsonResponse(
                        {
                            "status": "already_logged_in",
                            "message": f"Already logged in on {active_session.device_name or 'another device'}.",
                            "device_name": active_session.device_name
                            or "Another Device",
                        },
                        status=200,
                    )
                # force_logout=True → log out previous device and continue
                UserSession.objects.filter(user=user).update(is_active=False)

            # ? GENERATE TOKEN
            session_id = str(uuid.uuid4())
            refresh = RefreshToken.for_user(user)

            # ? CREATE / UPDATE SESSION
            UserSession.objects.filter(user=user).update(is_active=False)
            UserSession.objects.create(
                user=user,
                device_id=device_id,
                device_name=device_name,
                session_id=session_id,
                is_active=True,
            )

            # ? RESPONSE WITH TOKEN AND USER INFO
            return JsonResponse(
                {
                    "status": "success",
                    "token": str(refresh.access_token),
                    "session_id": session_id,
                    "user": {
                        "id": user.id,
                        "name": user.name,
                        "email": user.email,
                        "role": user.role,
                    },
                }
            )
        except Exception as e:
            print("SIGNIN ERROR:", str(e))
            traceback.print_exc()

            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# * =========================
# * LOGOUT
# * =========================
@csrf_exempt
def logout(request):
    if request.method == "POST":
        try:
            # UserSession.objects.filter(session_id=session_id).delete()

            data = json.loads(request.body)
            session_id = data.get("session_id")

            if session_id:
                UserSession.objects.filter(session_id=session_id).update(
                    is_active=False
                )
            return JsonResponse({"status": "success", "message": "Logged out"})

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)})


# =========================
# UPDATE ROLE
# =========================
@csrf_exempt
def update_role(request, pk):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            new_role = data.get("role")

            with transaction.atomic():
                customer = Customer.objects.select_for_update().get(id=pk)
                customer.role = new_role
                customer.save()

            return JsonResponse({"success": True, "message": "Role updated"})

        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid method"})


# =========================
# DELETE USER
# =========================
@csrf_exempt
def delete_user(request, pk):
    if request.method == "DELETE":
        try:
            customer = Customer.objects.get(id=pk)
            customer.delete()

            return JsonResponse(
                {"success": True, "message": "User deleted successfully"}
            )

        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid method"})


# =========================
# GET USERS
# =========================
def get_users(request):
    if request.method == "GET":
        customers = Customer.objects.exclude(role="demo")

        users_data = []
        for customer in customers:
            try:
                user_plan = UserPlan.objects.select_related("plan").get(
                    customer=customer
                )

                plan = user_plan.plan

                # =========================
                # CALCULATE USAGE DISPLAY
                # =========================
                usage_display = None

                if plan:
                    if plan.is_unlimited:
                        # Unlimited case
                        if plan.tool == "t1":
                            usage_display = f"{user_plan.t1_projects_used}/∞"
                        elif plan.tool == "t2":
                            usage_display = f"{user_plan.t2_projects_used}/∞"
                        elif plan.tool == "hybrid":
                            usage_display = f"{user_plan.t1_projects_used}/∞, {user_plan.t2_projects_used}/∞"

                    else:
                        # Limited case
                        if plan.tool == "t1":
                            usage_display = f"{user_plan.t1_projects_used}/{plan.t1_projects_limit or 0}"

                        elif plan.tool == "t2":
                            usage_display = f"{user_plan.t2_projects_used}/{plan.t2_projects_limit or 0}"

                        elif plan.tool == "hybrid":
                            usage_display = (
                                f"{user_plan.t1_projects_used}/{plan.t1_projects_limit or 0}, "
                                f"{user_plan.t2_projects_used}/{plan.t2_projects_limit or 0}"
                            )

                users_data.append(
                    {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                        "address": customer.address,
                        "password": customer.plain_password,
                        "is_active_account": customer.is_active_account,
                        "role": customer.role,
                        "plan_name": plan.name if plan else None,
                        "plan_id": plan.id if plan else None,
                        "plan_start_date": user_plan.start_date,
                        "plan_end_date": user_plan.end_date,
                        "plan_active": user_plan.active,
                        "project_usage": usage_display,
                    }
                )

            except UserPlan.DoesNotExist:
                users_data.append(
                    {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                        "address": customer.address,
                        "role": customer.role,
                        "password": customer.plain_password,
                        "plan_name": None,
                        "plan_id": None,
                        "plan_start_date": None,
                        "plan_end_date": None,
                        "plan_active": False,
                        "project_usage": None,
                    }
                )

        return JsonResponse({"status": "success", "users": users_data})


# =========================
# UPDATE USER (ALL FIELDS)
# =========================
@csrf_exempt
def update_user(request, pk):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            name = data.get("name")
            email = data.get("email")
            address = data.get("address")
            role = data.get("role")
            password = data.get("password")

            with transaction.atomic():
                customer = Customer.objects.select_for_update().get(id=pk)

                if name:
                    customer.name = name
                if email:
                    # Check if email is not taken by another user
                    if Customer.objects.filter(email=email).exclude(id=pk).exists():
                        return JsonResponse(
                            {"success": False, "message": "Email already in use"}
                        )
                    customer.email = email
                if address:
                    customer.address = address
                if role:
                    customer.role = role.lower()
                if password:
                    customer.set_password(password)
                    customer.plain_password = password
                customer.save()

            return JsonResponse(
                {
                    "success": True,
                    "message": "User updated successfully",
                    "user": {
                        "id": customer.id,
                        "name": customer.name,
                        "email": customer.email,
                        "address": customer.address,
                        "role": customer.role,
                        "password": customer.plain_password,
                    },
                }
            )

        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid method"})


# =========================
# DEMO APIs
# =========================


# GET ALL DEMO USERS
# =========================
@csrf_exempt
def get_demo_users(request):
    if request.method == "GET":
        demo_users = Customer.objects.filter(role="demo")
        users_data = []

        for user in demo_users:
            is_expired = user.demo_expires_at and user.demo_expires_at < now()

            # auto update in DB (optional but good)
            if is_expired and user.is_demo_active:
                user.is_demo_active = False
                user.save()

            users_data.append(
                {
                    "id": user.id,
                    "name": user.name,
                    "email": user.email,
                    "role": user.role,
                    "password": user.plain_password,
                    "is_active": False if is_expired else user.is_demo_active,
                    "expires_at": user.demo_expires_at,
                    "created_at": user.created_at,
                }
            )

        return JsonResponse({"status": "success", "users": users_data})

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=400)


# Generate random password for demo user
def generate_password():
    prefix = "Solarstr@"
    digits = random.randint(10000, 999999)
    return f"{prefix}{digits}"




# =========================
# CREATE DEMO REQUEST
# (saves user + generates password, but does NOT activate yet)
# =========================
@csrf_exempt
def create_demo_request(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            name = data.get("name")
            email = data.get("email")

            if not name or not email:
                return JsonResponse(
                    {"status": "error", "message": "Name and email are required"},
                    status=400,
                )

            # ? ALREADY HAS A DEMO (active or expired — one per email ever)
            if Customer.objects.filter(email=email, role="demo").exists():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "You already have a demo account. Please contact admin for access.",
                    },
                    status=400,
                )

            # ? GENERATE PASSWORD
            password = generate_password()

            # ? CREATE USER (inactive, not started yet)
            demo_user = Customer(
                name=name,
                email=email,
                role="demo",
                is_demo_active=False,   # not active until admin triggers
                plain_password=password,
            )
            demo_user.set_password(password)
            demo_user.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Demo request received. We will contact you shortly.",
                }
            )

        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)


# =========================
# ACTIVATE DEMO
# (admin calls this to start the 1-hour clock)
# =========================
@csrf_exempt
def activate_demo(request, pk):
    if request.method == "POST":
        try:
            demo_user = Customer.objects.get(id=pk, role="demo")

            # ? ALREADY ACTIVATED AND EXPIRED
            if demo_user.demo_expires_at and demo_user.demo_expires_at < now():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "This demo has already been used and expired. Cannot reactivate.",
                    },
                    status=400,
                )

            # ? ALREADY ACTIVE AND STILL RUNNING
            if demo_user.is_demo_active and demo_user.demo_expires_at and demo_user.demo_expires_at > now():
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Demo is already active.",
                    },
                    status=400,
                )

            # ? ACTIVATE — start 1 hour clock now
            demo_user.is_demo_active = True
            demo_user.demo_expires_at = now() + timedelta(minutes=60)
            demo_user.save()

            return JsonResponse(
                {
                    "status": "success",
                    "message": "Demo activated successfully. It will expire in 1 hour.",
                    "user": {
                        "id": demo_user.id,
                        "name": demo_user.name,
                        "email": demo_user.email,
                        "password": demo_user.plain_password,
                        "demo_expires_at": demo_user.demo_expires_at,
                    },
                }
            )

        except Customer.DoesNotExist:
            return JsonResponse({"status": "error", "message": "Demo user not found"}, status=404)
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

    return JsonResponse({"status": "error", "message": "Invalid method"}, status=405)



# DEACTIVATE / ACTIVATE USER (ADMIN FUNCTION)
# =========================
@csrf_exempt
def deactivate_user(request, pk):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            is_active = data.get("is_active", False)  # True=activate, False=deactivate

            customer = Customer.objects.get(id=pk)
            customer.is_active_account = is_active
            customer.save()

            # also kill active sessions if deactivating
            if not is_active:
                UserSession.objects.filter(user=customer).update(is_active=False)

            status_text = "activated" if is_active else "deactivated"
            return JsonResponse(
                {"success": True, "message": f"User {status_text} successfully"}
            )

        except Customer.DoesNotExist:
            return JsonResponse({"success": False, "message": "User not found"})
        except Exception as e:
            return JsonResponse({"success": False, "message": str(e)})

    return JsonResponse({"success": False, "message": "Invalid method"})
