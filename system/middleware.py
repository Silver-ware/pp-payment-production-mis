import re
from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.models import User
from .models import BusinessDetails, SystemSettings

class RestrictAllExceptAdminSignupMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignore requests for static files and favicon
        if re.match(r"^/(static/|favicon\.ico)", request.path):
            return self.get_response(request)

        # Check if a superuser exists
        superuser_exists = User.objects.filter(is_staff=True, is_active=True, is_superuser=True).exists()

        # Allow access to 'admin_signup' path even if no superuser exists
        admin_signup_path = reverse('admin_signup')  # Replace with your actual URL name
        if not superuser_exists and request.path != admin_signup_path:
            # Redirect to 'admin_signup' if no superuser exists and the path is not 'admin_signup'
            return redirect(admin_signup_path)

        # Continue processing the request if conditions are not met
        return self.get_response(request)

class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        exempt_urls = [settings.LOGIN_URL, '/admin/', '/setup/']

        # Kay demuntog ito na starts with ginexempt tanan na url pattern.
        # Explicit ine, kay para han root url
        if request.path == '/' or request.user.is_authenticated:
            return self.get_response(request)

        if not request.user.is_authenticated and not any(request.path.startswith(url) for url in exempt_urls):
            return redirect(f"{settings.LOGIN_URL}?next={request.path}")
        return self.get_response(request)

class RestrictLoginPathMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Define the restricted login path
        login_path = reverse('login')  # Adjust this to your login path name if different

        # Check if the user is authenticated and attempting to access the login path
        if request.user.is_authenticated and request.path == login_path:
            # Redirect authenticated users to the dashboard
            return redirect('dashboard')

        # Continue processing the request if the path is not restricted
        return self.get_response(request)
    
class RestrictSetupAdminRegisterMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Ignore requests for static files and favicon
        if re.match(r"^/(static/|favicon\.ico)", request.path):
            return self.get_response(request)

        # Check if the superuser exists
        superuser_exists = User.objects.filter(is_staff=True, is_active=True, is_superuser=True).exists()

        # Check if the requested path matches '/setup/admin/register'
        restricted_path = reverse('admin_signup')  # Change this to your actual URL name
        if superuser_exists and request.path == restricted_path:
            if request.user.is_authenticated:
                # If the user is authenticated, redirect to dashboard
                return redirect('dashboard')
            else:
                # If the user is not authenticated, redirect to login
                return redirect('login')

        # Continue processing the request if the path is not restricted
        return self.get_response(request)

class RestrictSetupPathsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if data exists in both BusinessDetails and SystemSettings models
        data_exists = (
            BusinessDetails.objects.exists() and
            SystemSettings.objects.exists()
        )

        # List of restricted setup paths
        restricted_paths = [
            reverse('business_details'),
            reverse('services_and_pricing'),
            reverse('equipment'),
            reverse('inventory_and_category'),
            reverse('supplier'),
            reverse('customer_prerecords'),
            reverse('system_settings'),
            reverse('save_to_database'),
        ]

        # Restrict access if data exists and the path matches any restricted path
        if data_exists and request.path in restricted_paths:
            if request.user.is_authenticated:
                # Redirect authenticated users to the dashboard
                return redirect('dashboard')
            else:
                # Redirect unauthenticated users to the login page
                return redirect('login')

        # Continue processing the request if conditions are not met
        return self.get_response(request)
