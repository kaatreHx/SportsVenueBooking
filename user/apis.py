from django.http import JsonResponse
from .sms_service import send_sms

def send_test_sms(request):
    success, message = send_sms(
        "+18777804236",  # VERIFIED number
        "Hello 👋 SMS from Django using Twilio!"
    )
    
    if success:
        return JsonResponse({"status": "Success", "message": message})
    else:
        return JsonResponse({
            "status": "Error",
            "message": message,
            "hint": "Check your Twilio Geo-Permissions for the destination country."
        }, status=400)
