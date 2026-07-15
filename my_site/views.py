import requests
from django.http import JsonResponse

def home(request):
    ip = requests.get("https://api.ipify.org").text

    return JsonResponse({
        "status": "online",
        "message": "Server is running 🚀",
        "ip_address": ip
    })
    


def health_check(request):
    return JsonResponse({"status": "Online","message": "Server is running 🚀",})