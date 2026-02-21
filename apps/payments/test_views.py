from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@csrf_exempt
@api_view(["GET", "POST"])
@permission_classes([AllowAny])
def webhook_health_check(request):
    """
    Simple health check endpoint for webhook testing.
    No signature verification - just confirms the endpoint is reachable.
    """
    return JsonResponse(
        {
            "status": "ok",
            "message": "Razorpay webhook endpoint is reachable",
            "method": request.method,
            "path": request.path,
        },
        status=200,
    )
