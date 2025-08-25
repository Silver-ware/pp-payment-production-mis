from django.urls import path
from . import views


urlpatterns = [
    path('', views.admin_auth),
    path("accounts/signup/", views.SignUpView.as_view(), name="signup"),
    path('accounts/login/', views.CustomLoginView.as_view(), name="login"),
    path('logout/', views.CustomLogoutView.as_view(), name="logout"),
    
    path("setup/admin/register", views.admin_signup, name='admin_signup'),
    path('setup/business-details/', views.business_details, name='business_details'),
    path('setup/services-and-pricing/', views.services_and_pricing, name='services_and_pricing'),
    path('setup/equipments/', views.equipment, name='equipment'),
    path('setup/inventory-and-category/', views.inventory_and_category, name='inventory_and_category'),
    path('setup/supplier/', views.supplier, name='supplier'),
    path('setup/customer_prerecords/', views.customer_prerecords, name='customer_prerecords'),
    path('setup/system_settings/', views.system_settings, name='system_settings'),
    path('setup/save_to_database/', views.save_to_database, name='save_to_database'),

    path('verify-superuser/', views.verify_superuser, name='verify_superuser'),
    path('dashboard', views.dashboard, name="dashboard"),  
    
    path('orders', views.orders_view, name="orders"),
    path('authorize-cancel/', views.authorize_cancel, name='authorize_cancel'),
    path('orders/update_order_queue/', views.update_order_queue, name='update_order_queue'),
    path('refresh-order-queue/', views.refresh_order_queue, name='refresh_order_queue'),
    path('orders/<int:order_id>/cancel/', views.cancel_order, name='cancel_order'),
    path('get_paginated_orders/', views.get_paginated_orders, name='get_paginated_orders'),
    path('get-customization-options/', views.get_customization_options, name='get_customization_options'),
    path('get-pricing-options/', views.get_pricing_options, name='get_pricing_options'),
    path('orders/search/', views.search_orders, name='search_orders'),

    path('production/', views.production, name="production"),  
    path('submit-production/', views.submit_production, name='submit_production'),
    path('fetch-materials/', views.fetch_materials, name='fetch_materials'),
    path('filter/production-by-priority/', views.filter_by_priority, name='filter_by_priority'),
    path('filter/production-by-status/', views.filter_by_status, name='filter_by_status'),
    path("fetch/quality-checks/<int:production_id>/", views.fetch_quality_checks, name="fetch_quality_checks"),
    path('get_quality_check/<int:job_id>/<str:parameter>/', views.get_quality_check, name='get_quality_check'),
    path('save_quality_check/<int:job_id>/<str:parameter>/', views.save_quality_check, name='save_quality_check'),
    path("production/search/", views.search_production, name="search_production"),
    path("inventory/management/", views.inventory_management, name="inventory_management"),
    path("inventory/alerts/", views.inventory_alerts, name="inventory_alerts"),
    path("contact-supplier/", views.contact_supplier, name="contact_supplier"),
    # path('production/<order_id>', views.production, name="production"),

    path('payment/', views.payment, name="payment"),    
    path('new_payment/', views.new_payment, name='new_payment'),

    path('crm/', views.crm_view, name='crm_view'),
    path('estimates/v2', views.estimatesv2, name="estimatesv2"),   
]