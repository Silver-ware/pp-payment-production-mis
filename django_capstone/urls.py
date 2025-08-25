from django.contrib import admin
from django.urls import include, path   

urlpatterns = [
    path('admin/', admin.site.urls),
    path("__reload__/", include("django_browser_reload.urls")), # For auto-reload
    path('accounts/', include('system.urls')), # For accounts/signup
    path('', include('system.urls')),
    path("accounts/", include("django.contrib.auth.urls")),  # For logout & login
]
