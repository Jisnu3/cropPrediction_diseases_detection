from django.contrib.auth import logout
from django.shortcuts import redirect
from django.contrib import messages

class BlockedUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # If the user is authenticated but has been marked inactive (blocked) in the DB
        if request.user.is_authenticated and not request.user.is_active:
            logout(request)
            messages.error(request, "Your account has been blocked by the administrator.")
            return redirect('login')
            
        response = self.get_response(request)
        return response
