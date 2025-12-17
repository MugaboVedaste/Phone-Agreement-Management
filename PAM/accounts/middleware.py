from django.shortcuts import redirect
from django.urls import reverse


class SuspensionMiddleware:
    """
    Middleware to redirect suspended users to the hold page.
    Prevents suspended users from accessing any part of the system except logout.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
        # URLs that suspended users can access
        self.allowed_urls = [
            reverse('hold'),
            reverse('logout'),
        ]
    
    def __call__(self, request):
        # Check if user is authenticated and suspended
        if request.user.is_authenticated and hasattr(request.user, 'is_suspended'):
            if request.user.is_suspended:
                # Allow access to hold page and logout
                if request.path not in self.allowed_urls:
                    return redirect('hold')
        
        response = self.get_response(request)
        return response
