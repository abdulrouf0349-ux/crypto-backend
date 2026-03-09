from django.http import JsonResponse
from .models import AuthToken

def token_required(view_func):
    def wrapper(request, *args, **kwargs):
        # Allow preflight requests to pass
        if request.method == "OPTIONS":
            return JsonResponse({}, status=200)

        token = request.headers.get('Authorization')
        if not token:
            return JsonResponse({'error': 'Token missing'}, status=401)
        
        if not AuthToken.objects.filter(token=token).exists():
            return JsonResponse({'error': 'Invalid token'}, status=403)
        
        return view_func(request, *args, **kwargs)
    return wrapper
