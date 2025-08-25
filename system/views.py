from django.core.paginator import Paginator
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.shortcuts import render, redirect, resolve_url
from django.urls import reverse_lazy, reverse
from django.views import View
from django.views.generic import CreateView
from django.http import JsonResponse
from django.utils.timezone import now

import logging
from django.template.loader import render_to_string
from django.contrib.auth.models import User  
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.db import transaction
from .models import BusinessDetails, Service, CustomizationOption, PricingOption
from .models import (
  Equipment, InventoryCategory, Supplier, Inventory, Customer, SystemSettings, Order 
)
from .forms import CustomUserCreationForm, AuthenticationForm, BusinessDetailsForm, ServiceForm
from .forms import PricingOptionForm, EquipmentForm, InventoryForm, SupplierForm, CustomerForm, SystemSettingsForm, OrderForm

# Kinda useless maderfacker now
def admin_auth(request): #Check if there's a superuser in the User Model 
  if User.objects.filter(is_staff=True, is_active=True, is_superuser=True).exists():
    return redirect('login')
  else:
    return redirect('admin_signup')

def admin_signup(request):
  if request.method == "POST":
      # print(request.POST)
      form = CustomUserCreationForm(request.POST)
      form.fields['role'].required = False
      if form.is_valid():
        user = form.save(view_name="admin_signup") #Pass the view_name
        return redirect('/')
      # return HttpResponseRedirect(reverse('login'))
  else:
      form = CustomUserCreationForm()
  return render(request, "admin_signup.html", {"form": form})

class CustomLoginView(LoginView):
    form_class = AuthenticationForm
    template_name = 'registration/login.html'

    def form_valid(self, form):
        # Get the authenticated user
        user = form.get_user()

        # Check if it's the first login for a superuser
        if user.is_superuser and user.is_staff and user.is_active and user.last_login is None:
            # Log the user in and redirect to signup
            login(self.request, user)
            print("First Time Loggin in.")
            return redirect('signup')  # Use redirect instead of resolve_url

        # If not the first login, proceed with the default behavior
        return super().form_valid(form)

    def form_invalid(self, form):
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        # Redirect to the dashboard for all valid logins
        return resolve_url('dashboard')
    
class CustomLogoutView(LogoutView):
    next_page = '/accounts/login'

class SignUpView(SuccessMessageMixin, CreateView):
    model = User
    form_class = CustomUserCreationForm
    success_url = reverse_lazy("signup")
    template_name = "registration/signup.html"

    def form_valid(self, form):
        messages.success(
          self.request,
          "Employee account created successfully.<br>Do you want to add another?"
        )
        return super().form_valid(form)
    def form_invalid(self, form):
        # Render the form with errors
        return self.render_to_response(self.get_context_data(form=form))

def business_details(request):
    session_data = request.session.get('business_details', {})
    
    if 'business_details' in request.session:
        print("Session Data:", request.session['business_details'])  # Debugging purpose

    # Handle the GET request to display the form
    if request.method == 'GET':
        # Initialize form with existing session data (if any)
        form = BusinessDetailsForm(initial=session_data)
        return render(request, 'setup/business_details.html', {'form': form, 'session_data': session_data})

    # Handle the POST request to process and save the form data in the session
    elif request.method == 'POST':
        form = BusinessDetailsForm(request.POST, request.FILES)
        if form.is_valid():
            # Save form data to session (not database yet)
            request.session['business_details'] = form.cleaned_data
            # messages.success(request, "Business details saved!")
            return redirect('services_and_pricing')  # Redirect to next step
        # If form is invalid, re-render the form with error messages
        else:
            # messages.error(request, "Please correct the errors below.")
            return render(request, 'setup/business_details.html', {'form': form})

def services_and_pricing(request):
    # For resetting purposes
    # request.session['services_data'] = [] 
    
    # Initialize session data
    if 'services_data' not in request.session:
        request.session['services_data'] = []

    print(request.session.get('services_data'))

    unlocked=False
    if(request.session['services_data'] != []):
        unlocked=True

    # Service Form
    service_form = ServiceForm()
    pricing_option_form = PricingOptionForm()

    # Handle POST
    if request.method == 'POST':
        if 'add_service' in request.POST:
            service_form = ServiceForm(request.POST)
            if service_form.is_valid():
                # Save service data in session
                customization_options = [
                    {'name': option, 'pricing_options': []} 
                    for option in service_form.cleaned_data['customization_options']
                ]
                # Save service data in session with structured customization options
                service_data = {
                    'name': service_form.cleaned_data['name'],
                    'customization_options': customization_options,
                }

                # Append the new service data to the services_data list in the session
                services_data = request.session.get('services_data', [])
                services_data.append(service_data)
                request.session['services_data'] = services_data

                # Optionally keep the current_service for additional processing
                request.session['current_service'] = service_data
                request.session.modified = True 

                success_message = f"Service: '{service_data['name']}' added successfully!"

                additional_data = {"reload_script": True}
                unlocked = {"unlocked": True}
                # Debugging: Check session data
                print("Updated services_data:", request.session['services_data'])
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'success',
                        'add_service': True,
                        'service_form_html': render_to_string('setup/partials/service_form.html', {'service_form': ServiceForm(), **additional_data, **unlocked}),
                        'success_message': success_message,
                    })
            else:
                # If form is invalid, return errors back to the client
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'status': 'error',
                        'service_form_html': render_to_string('setup/partials/service_form.html', {'service_form': service_form}),
                    })

        elif 'add_pricing_option' in request.POST:
              # Retrieve the services data stored in the session
              services_data = request.session.get('services_data', [])
              print("Services Data:", services_data)  # Debugging
              print("Type of services_data:", type(services_data))  # List kaba na piste ka

              # Get the service index and customization option from the POST data
              service_index = request.POST.get('service_index')
              customization_option_name = request.POST.get('customization_option')  # The selected customization option name
              description = request.POST.get('description')
              price = request.POST.get('price')

              # Ensure service_index is provided and valid
              try:
                  service_index = int(service_index)
              except (TypeError, ValueError):
                  return JsonResponse({'status': 'error', 'message': 'Invalid service index provided.'})

              # Ensure the service index exists in the session
              if service_index >= len(services_data):
                  return JsonResponse({'status': 'error', 'message': 'Service index out of range.'})

              # Retrieve the current service
              current_service = services_data[service_index]
              print("Current Service:", current_service)

              # Find the relevant customization option within the current service
              customization_option = next(
                  (opt for opt in current_service['customization_options'] if opt['name'] == customization_option_name),
                  None
              )

              if customization_option:
                  print("Customization Option Found:", customization_option)
                  
                  # Create the pricing data structure
                  pricing_data = {
                      'description': description,
                      'price': float(price) if price else 0.0,
                  }

                  # Add the pricing data to the relevant customization option
                  customization_option.setdefault('pricing_options', []).append(pricing_data)

                  # Save the updated services data back to the session
                  request.session['services_data'] = services_data
                  request.session.modified = True

                  # Debugging updated service structure
                  print("Updated Service Data:", services_data)

                  service_tabs_html = render_to_string('setup/partials/service_tabs.html', {'services_data': services_data})
                  # print("Updated Service Tabs HTML:", service_tabs_html)  # Debugging
                  if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                      print("Ajax Operation")
                      return JsonResponse({
                          'status': 'success',
                          'add_pricing_option': True,
                          'service_tabs_html': service_tabs_html,
                          'success_message': 'Pricing option added successfully!',
                          'active_tab_index': service_index,
                      })
                  else:
                      print("Not Ajax Operation")
              else:
                  # Handle case where the customization option was not found
                  return JsonResponse({
                      'status': 'error',
                      'message': 'Customization option not found.',
                  })

        elif 'save_service' in request.POST:
          # Get the current service and save it to services_data
            current_service = request.session.pop('current_service', None)
            if current_service:
              # Avoid duplicates by ensuring current_service is not already in services_data
              services_data = request.session.get('services_data', [])
              if current_service not in services_data:
                  services_data.append(current_service)
                  request.session['services_data'] = services_data
                  request.session.modified = True
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
              return JsonResponse({
                  'status': 'success',
                  'confirm_services': True,
                  'service_tabs_html': render_to_string('setup/partials/service_tabs.html', {'services_data': request.session['services_data']}), 
              })
        if 'revert_to_service' in request.POST:
            # Prepare the service form to be sent back to the client
            additional_data = {"reload_script": True}

            # Render the service form with the additional data
            service_form_html = render_to_string(
                'setup/partials/service_form.html',
                {'service_form': ServiceForm(), **additional_data}
            )
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
              print("Ajax Reverted")
              return JsonResponse({
                'status': 'success',
                'newTagtify': True,
                'service_form_html': service_form_html,
                })
            

    # Render template
    return render(request, 'setup/services_and_pricing.html', {
        'unlocked': unlocked,
        'service_form': service_form,
        'pricing_option_form': pricing_option_form,
        'current_service': request.session.get('current_service', {}),
        'services_data': request.session.get('services_data', []),
    })


def equipment(request):
    # request.session['equipment'] = []
    # For debugging: Display session data
    if 'equipment' in request.session:
        print("Equipment Data:", request.session['equipment'])

    if 'equipment' not in request.session:
        request.session['equipment'] = []

    unlocked=False
    if(request.session['equipment'] != []):
        unlocked=True

    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment_data = form.cleaned_data
            # Store the data in the session
            request.session['equipment'].append(equipment_data)
            request.session.modified = True

            # Add a success message
            messages.success(request, f"Equipment '{equipment_data['name']}' added successfully!")
            return redirect('equipment')  # Assumes 'equipment' is the name of this view's URL pattern
        else:
            return render(request, 'setup/equipment.html', {'form': form})

    else:
        form = EquipmentForm()

    return render(request, 'setup/equipment.html', {'form': form, 'unlocked': unlocked})

def inventory_and_category(request):
    #  request.session['inventory'] = {}
    
    if 'inventory' in request.session:
        print("Inventory Data:", request.session['inventory'])
    
    if 'inventory' not in request.session:
        request.session['inventory'] = {}
        
    unlocked=False
    if(request.session['inventory'] != {}):
        unlocked=True

    inventory_data = request.session.get('inventory', {})

    # Transform inventory data into a list of categories and items
    categories = []
    for category_name, items in inventory_data.items():
        categories.append({
            'category_name': category_name,
            'materials': items
        })
    
    if request.method == 'POST':
        form = InventoryForm(request.POST)
        if form.is_valid():
            print("Valid!")
            inventory_data = form.cleaned_data
            
            category = inventory_data['category']
            if category not in request.session['inventory']:
                request.session['inventory'][category] = []
            
            # Add item to category
            request.session['inventory'][category].append({
                'name': inventory_data['name'],
                'unit': inventory_data['unit_of_measurement'],
                'stock_level': inventory_data['stock_level'],
                'reorder_threshold': inventory_data['reorder_threshold'],
                'supplier': inventory_data['supplier'],
                
            })
            request.session.modified = True
            messages.success(request, f"{inventory_data['name']} added successfully to {category}!")
            print("sds")
            return redirect('inventory_and_category')
        else:
            return render(request, 'setup/inventory_and_category.html', {'form': form})
    else:
        form = InventoryForm()

    return render(request, 'setup/inventory_and_category.html', {
        'unlocked': unlocked,
        'form': form,
        'categories': categories,
    })

# # views.py (Supplier) OPTIONAL
def supplier(request):
    if 'supplier' in request.session:
        print("Supplier Data:", request.session['supplier'])

    if 'supplier' not in request.session:
                request.session['supplier'] = []

    unlocked=True
    if request.method == 'POST':
        form = SupplierForm(request.POST)
        if form.is_valid():
            supplier_data = form.cleaned_data

            # Initialize the session key if it doesn't exist
            

            # Append the new data to the list
            request.session['supplier'].append(supplier_data)
            request.session.modified = True  # Ensure the session is marked as modified

            # Show a success message
            messages.success(request, 'Supplier data saved successfully!')

            # Redirect to the same page to review or modify data
            return redirect('supplier')
        else:
            return render(request, 'setup/setup.html', {'form': form})
    else:
        # Check if there's already data in the session
        # supplier_data = request.session.get('supplier', None)
        # if supplier_data:
        #     form = SupplierForm(initial=supplier_data[-1])  # Prefill form with last entry (if any)
        # else:
            form = SupplierForm()
    return render(request, 'setup/supplier.html', {'form': form, 'unlocked': unlocked})


# # views.py (Customer) OPTIONAL
def customer_prerecords(request):
    # request.session['customer'] = []
    if 'customer' in request.session:
        print("Customer Data:", request.session['customer'])

    # Ensure the session data for 'customer' is a list and append the new data
    if 'customer' not in request.session:
        request.session['customer'] = []
    
    unlocked=True
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            # Get the cleaned data from the form
            customer_data = form.cleaned_data
            
            request.session['customer'].append(customer_data)
            request.session.modified = True  # Ensure the session is updated

            # Show a success message
            messages.success(request, 'Customer data saved successfully!')

            # Redirect to the same page to review or modify data
            return redirect('customer_prerecords')
        else:
             return render(request, 'setup/customer_prerecords.html', {'form': form})
    else:
        # Prefill form if there is existing data in the session
        customer_data = request.session.get('customer', None)
        if customer_data:
            form = CustomerForm(initial=customer_data[-1])  # Prefill form with the most recent data
        else:
            form = CustomerForm()

    return render(request, 'setup/customer_prerecords.html', {'form': form, 'unlocked': unlocked})

# views.py (System Settings)
def system_settings(request):
    if 'system_settings' in request.session:
        print("Settings:", request.session['system_settings'])
    if request.method == "POST":
        form = SystemSettingsForm(request.POST)
        if form.is_valid():
            # Save form data to the session
            request.session['system_settings'] = form.cleaned_data

            # If AJAX request, send session data via JSON
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'modal_data': request.session.get('system_settings', {}),
                    'message': "System settings saved successfully. Please review all data before proceeding.",
                })
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'form_errors': form.errors,
                })
    else:
        form = SystemSettingsForm()
    
    system_settings = request.session.get('system_settings', {})
    formatted_settings = {key.replace('_', ' ').capitalize(): value for key, value in system_settings.items()}
    # Retrieve all session data
    session_data = {
        'business_details': request.session.get('business_details', {}),
        'services_data': request.session.get('services_data', []),
        'equipment': request.session.get('equipment', []),
        'inventory': request.session.get('inventory', {}),
        'supplier': request.session.get('supplier', []),
        'customer': request.session.get('customer', []),
        'system_settings': formatted_settings,
        'smtp': system_settings
    }
    return render(request, 'setup/system_settings.html', {
        'form': form,
        'modal_data': session_data,
    })

def save_to_database(request):
    """Handles saving session data to models when 'Add to Database' is clicked."""
    try:
        with transaction.atomic():  # Ensure all data is saved atomically

            # 1. Save Business Details
            business_details = request.session.get('business_details', {})
            if business_details:
                BusinessDetails.objects.create(
                    name=business_details['business_name'],
                    address=business_details['business_address'],
                    contact_number=business_details['contact_number'],
                    email=business_details['email'],
                    tax_identification_number=business_details['tin'],
                    logo=business_details.get('logo'),
                )

            # 2. Save Services, Customization Options, and Pricing Options
            services_data = request.session.get('services_data', [])
            for service_data in services_data:
                # 1. Create the Service instance
                service = Service.objects.create(name=service_data['name'])

                # 2. Create or get the CustomizationOption instances
                customization_options = []
                for option in service_data['customization_options']:
                    # Convert the option name to lowercase to avoid duplicates
                    option_name = option['name'].lower()

                    # Get or create the CustomizationOption
                    customization_option, _ = CustomizationOption.objects.get_or_create(
                        name=option_name
                    )
                    customization_options.append(customization_option)

                    # 3. Create the PricingOption objects for this CustomizationOption
                    for pricing in option.get('pricing_options', []):
                        # Create the PricingOption with the Service instance
                        PricingOption.objects.create(
                            service=service,  # Use the created Service instance
                            customization_option=customization_option,
                            description=pricing['description'],
                            price=pricing['price'],
                        )

                # 4. Associate CustomizationOptions with the Service
                service.customization_options.set(customization_options)


            # 3. Save Equipment
            equipment_data = request.session.get('equipment', [])
            for equipment in equipment_data:
                Equipment.objects.create(
                    name=equipment['name'],
                    description=equipment.get('description'),
                    condition=equipment['condition'],
                )

            # 4. Save Inventory and Related Data
            inventory_data = request.session.get('inventory', {})
            for category_name, materials in inventory_data.items():
                # Ensure category is unique
                category, _ = InventoryCategory.objects.get_or_create(
                    category_name=category_name
                )
                for material in materials:
                    # Ensure supplier is unique if provided
                    supplier = None
                    if material.get('supplier'):
                        supplier, _ = Supplier.objects.get_or_create(
                            supplier_name=material['supplier']
                        )

                    # Save inventory material
                    Inventory.objects.create(
                        name=material['name'],
                        category=category,
                        stock_level=material['stock_level'],
                        reorder_threshold=material['reorder_threshold'],
                        supplier=supplier,
                        unit_of_measurement=material['unit'],
                    )

            # 5. Save Suppliers
            suppliers_data = request.session.get('supplier', [])
            for supplier_data in suppliers_data:
                supplier, created = Supplier.objects.get_or_create(
                    supplier_name=supplier_data['supplier_name'],
                    defaults={
                        'contact_person': supplier_data.get('contact_person'),
                        'phone_number': supplier_data.get('phone_number'),
                        'email': supplier_data.get('email'),
                        'address': supplier_data.get('address'),
                        'additional_info': supplier_data.get('additional_info'),
                    },
                )
                if not created:  # Update existing supplier with any missing fields
                    for key, value in supplier_data.items():
                        if not getattr(supplier, key) and value:
                            setattr(supplier, key, value)
                    supplier.save()

            # 6. Save Customers
            customers_data = request.session.get('customer', [])
            for customer_data in customers_data:
                Customer.objects.create(
                    name=customer_data['name'],
                    contact_number=customer_data['contact_number'],
                    email=customer_data['email'],
                    address=customer_data.get('address', ""),
                )

            # 7. Save System Settings
            system_settings = request.session.get('system_settings', {})
            if system_settings:
                SystemSettings.objects.update_or_create(
                    smtp_email=system_settings['smtp_email'],
                    defaults={
                        'smtp_server': system_settings['smtp_server'],
                        'smtp_port': system_settings['smtp_port'],
                        'smtp_password': system_settings['smtp_password'],
                    },
                )

            # Clear session data after saving
            # request.session.clear()
            print("DB Save!")
            return JsonResponse({
                'success': True,
                'message': 'All data has been successfully saved to the database.',
                'redirect_url': '/dashboard'  # Replace with the actual dashboard URL
            })

    except Exception as e:
        # Log the error for debugging
        logging.error(f"Error saving data to database: {e}")
        return JsonResponse({
            'success': False,
            'error': str(e),
            'message': 'An error occurred while saving the data.'
        })

    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
@login_required
def verify_superuser(request):
    print(f"User: {request.user}") 
    # Check if the user is authenticated and return superuser status
    if request.user.is_authenticated:
        return JsonResponse({"is_superuser": request.user.is_superuser})
    else:
        return JsonResponse({"is_superuser": False}, status=HttpResponseForbidden.status_code)


from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count
from django.utils.timezone import now
from .models import Payment, Inventory, Order, Production

def dashboard(request):
    # Total revenue from completed payments
    total_revenue = Payment.objects.filter(status='PAID').aggregate(total=Sum('amount'))['total'] or 0

    # Overdue payments from completed production jobs with pending payments
    completed_production_orders = Production.objects.filter(status='COMPLETED').values_list('order_id', flat=True)
    overdue_payments = (
        Payment.objects.filter(order_id__in=completed_production_orders, status='PENDING')
        .aggregate(total=Sum('amount'))['total'] or 0
    )

    # Inventory items with low stock
    low_stock_items = Inventory.objects.filter(stock_level__lt=F('reorder_threshold'))
    print(low_stock_items)

    # Recent orders (last 5)
    recent_orders = Order.objects.order_by('-created_at')[:5]

    pending_tasks = Production.objects.filter(
        Q(status='IN_PROGRESS') | Q(status='ON_HOLD'),
        priority='HIGH'
    ).select_related('order__customer', 'order__service')  # Optimize querying related data

    # Retrieve the relevant data from the production, including customer and service
    pending_task_data = pending_tasks.values(
        'job_id', 'status', 'priority', 
        'order__customer__name',  # Assuming `Customer` model has a `name` field
        'order__service__name'    # Assuming `Service` model has a `name` field
    )

    # print(pending_task_data)
    # Dynamic data for charts
    # Revenue over months
    monthly_revenue = (
        Payment.objects.filter(status='PAID')
        .annotate(month=TruncMonth('payment_date'))
        .values('month')
        .annotate(total=Sum('amount'))
        .order_by('month')
    )
    revenue_labels = [entry['month'].strftime('%b %Y') for entry in monthly_revenue]
    revenue_data = [entry['total'] for entry in monthly_revenue]

    # Order status breakdown
    order_status_data = Order.objects.values('status').annotate(count=Count('order_id')).order_by('status')
    order_status_counts = [status['count'] for status in order_status_data]
    order_status_labels = ['Pending', 'In Progress', 'Completed', 'Cancelled']  # Adjust labels as per your data

    context = {
        'total_revenue': float(total_revenue),
        'overdue_payments': float(overdue_payments),
        'low_stock_items': low_stock_items,
        'recent_orders': recent_orders,
        'pending_tasks': pending_task_data,
        'revenue_data': revenue_data,
        'revenue_labels': revenue_labels,
        'order_status_data': order_status_counts,
        'order_status_labels': order_status_labels,
    }
    # print(context)

    return render(request, 'dashboard.html', context)


from django.db import models
def orders_view(request):
    services = Service.objects.all()
    customers = Customer.objects.all()  # Fetch all customers

    if request.method == 'POST':
        customer_name = request.POST.get('name')
        order_form = OrderForm(request.POST)
        
        if customer_name.isdigit():
            try:
                # Fetch the customer by ID (digit-based)
                customer = Customer.objects.get(customer_id=customer_name)
            except Customer.DoesNotExist:
                messages.error(request, "Customer not found.")
                return redirect('orders')  # Redirect back if customer doesn't exist
        else:
            # If not a digit, proceed with the customer form
            customer_form = CustomerForm(request.POST)

            if customer_form.is_valid():
                # Save or get customer data
                customer_data = customer_form.cleaned_data
                customer, created = Customer.objects.get_or_create(
                    name=customer_data['name'],
                    defaults={
                        'contact_number': customer_data['contact_number'],
                        'email': customer_data['email'],
                        'address': customer_data['address'],
                    }
                )
        # Check if the order form is valid
        if order_form.is_valid():
            # Create the order with the customer reference
            order = order_form.save(commit=False)
            order.customer = customer
            order.status = 'PENDING'  # Ensuring status is set to PENDING

            # Get the max order queue number and assign the next value
            max_order_queue = Order.objects.aggregate(max_queue=models.Max('order_queue'))['max_queue'] or 0
            order.order_queue = max_order_queue + 1  # Assign the next queue number

            # Save the order
            order.save()

            # Use Django messages to pass success information
            messages.success(
                request,
                f"Order #{order.order_id} has been"
            )
            return redirect('orders')

        else:
            # Print errors for debugging
            print("Invalid")
            print("Customer Form Errors:", customer_form.errors)
            print("Order Form Errors:", order_form.errors)

    else:
        customer_form = CustomerForm()
        order_form = OrderForm()
        
    pending_progress_orders = Order.objects.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')
    completed_cancelled_orders = Order.objects.filter(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')

    # Paginate the pending and progress orders - Display 10 orders per page
    paginator_pp = Paginator(pending_progress_orders, 10)
    page_number_pp = request.GET.get('page_pp')
    paginated_pp = paginator_pp.get_page(page_number_pp)

    # Paginate the completed and cancelled orders - Display 10 orders per page
    paginator_cc = Paginator(completed_cancelled_orders, 10)
    page_number_cc = request.GET.get('page_cc')
    paginated_cc = paginator_cc.get_page(page_number_cc)

    return render(request, 'orders.html', {
        'customer_form': customer_form,
        'order_form': order_form,
        'services': services,
        'customer': customers,
        'current_date': now().strftime('%B %d, %Y'),
        'pending_progress': paginated_pp,
        'completed_cancelled': paginated_cc,
    })

from django.shortcuts import get_object_or_404
from django.utils import timezone
@login_required
def cancel_order(request, order_id, is_authorized=False):
    order = get_object_or_404(Order, order_id=order_id)
    # print(order)

    if order.status != "CANCELLED" and (request.user.is_superuser or is_authorized):
        try:
            # Update order status to cancelled and queue
            order.status = "CANCELLED"
            order.order_queue = None 
            order.completed_or_cancelled = timezone.now()
            order.save()

            # Re-sort the orders after cancellation
            # Fetch the updated list of non-cancelled, non-completed orders and re-order them
            pending_progress_orders = Order.objects.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')
            
            # Reassign the `order_queue` for each order in the list
            for index, order in enumerate(pending_progress_orders):
                order.order_queue = index + 1  # Reassign the queue position (1-based index)
                order.save()

            # Get the page number from the POST data, default to 1 if not provided
            page_number_pp = request.POST.get('page_pp', 1)

            # Paginate the updated list of orders
            paginator_pp = Paginator(pending_progress_orders, 10)
            paginated_pp = paginator_pp.get_page(page_number_pp)

            # Render the updated orders queue
            rendered_pp = render_to_string('includes/orders_queue.html', {'pending_progress': paginated_pp}, request=request)

            return JsonResponse({
                "success": True,
                "message": "Order successfully ",
                "orders_queue": rendered_pp
            })
        except Exception as e:
            # Handle unexpected errors
            return JsonResponse({
                "success": False,
                "message": f"An error occurred: {str(e)}"
            }, status=500)

    else:
        print("Not Super User!")
        return JsonResponse({
            "success": False,
            "message": "You are not authorized to cancel this order."
        }, status=403)

from .forms import SuperuserAuthenticationForm
from django.contrib.auth import authenticate
@login_required
def authorize_cancel(request):
    if request.method == "POST":
        form = SuperuserAuthenticationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            print(user)
            
            if user is not None and user.is_superuser:
                # Extract the order ID from the POST data
                order_id = request.POST.get('order_id')
                if not order_id:
                    print("No ID")
                    return JsonResponse({'status': 'error', 'message': 'Order ID not provided.'}, status=400)

                # Call the cancel_order view directly
                print(order_id)
                response = cancel_order(request, order_id, is_authorized=True)
                print(response)
                return response  # Return the JsonResponse from the cancel_order view
            else:
                print("Not Auth")
                return JsonResponse({'status': 'error', 'message': 'Invalid superuser credentials.'}, status=403)
        else:
            print("Form Errors:", form.errors)
            return JsonResponse({'status': 'error', 'message': 'Invalid form submission.'}, status=400)

    return JsonResponse({'error': 'Invalid request method'}, status=405)


from django.views.decorators.http import require_POST
@login_required
@require_POST
def update_order_queue(request):
    if request.user.is_superuser:
        # Get the order list from the POST data
        new_order = request.POST.getlist('order[]')  # Assuming 'order' is passed as a list
        
        # Get the current page number (default to 1 if not provided)
        page_number_pp = int(request.POST.get('page_pp', 1))
        items_per_page = 10
        # Calculate the starting position for the order_queue
        start_position = (page_number_pp - 1) * items_per_page + 1

        # Update the order_queue for each order
        for index, order_id in enumerate(new_order):
            order = Order.objects.get(order_id=order_id)
            order.order_queue = start_position + index  # Set the new order_queue position
            order.save()

        # Fetch the updated order queue
        pending_progress_orders = Order.objects.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')
        paginator_pp = Paginator(pending_progress_orders, 10)
        paginated_pp = paginator_pp.get_page(page_number_pp)

        # Render the updated orders queue HTML
        updated_html = render_to_string('includes/orders_queue.html', {'pending_progress': paginated_pp}, request=request)

        return JsonResponse({
            "success": True,
            "message": "Order queue updated successfully.",
            "orders_queue": updated_html  # Return the new HTML to update the #order-queue
        })
    else:
        return JsonResponse({
            "success": False,
            "message": "You are not authorized to update the order queue."
        }, status=403)
@login_required
def refresh_order_queue(request):
    if request.method == "GET":
        pending_progress_orders = Order.objects.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')

        page_number_pp = request.POST.get('page_pp', 1)
        paginator_pp = Paginator(pending_progress_orders, 10)
        paginated_pp = paginator_pp.get_page(page_number_pp)

        rendered_pp = render_to_string('includes/orders_queue.html', {'pending_progress': paginated_pp}, request=request)
        return JsonResponse({"orders_queue": rendered_pp})

    return JsonResponse({"error": "Invalid request method."}, status=400)




def get_paginated_orders(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if AJAX
        if request.GET.get('page_pp'):
            pending_progress_orders = Order.objects.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')
            paginator_pp = Paginator(pending_progress_orders, 10)
            page_number_pp = request.GET.get('page_pp')
            paginated_pp = paginator_pp.get_page(page_number_pp)
            html = render_to_string('includes/orders_queue.html', {'pending_progress': paginated_pp}, request=request)
        if request.GET.get('page_cc'):
            completed_cancelled_orders = Order.objects.filter(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')
            paginator_cc = Paginator(completed_cancelled_orders, 10)
            page_number_cc = request.GET.get('page_cc')
            paginated_cc = paginator_cc.get_page(page_number_cc)
            html = render_to_string('includes/orders_completed.html', {'completed_cancelled': paginated_cc}, request=request)


        return JsonResponse({'html': html}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

def get_customization_options(request):
    """AJAX view to fetch customization options for a selected service."""
    service_id = request.GET.get('service_id')
    try:
        service = Service.objects.get(pk=service_id)
        options = service.customization_options.values('id', 'name')
        return JsonResponse({'options': list(options)})
    except Service.DoesNotExist:
        return JsonResponse({'error': 'Service not found'}, status=404)

def get_pricing_options(request):
    if request.method == 'GET' and (request.headers.get('X-Requested-With') == 'XMLHttpRequest'):
        service_id = request.GET.get('service_id')
        customization_ids = request.GET.getlist('customization_ids[]')

        if not service_id or not customization_ids:
            return JsonResponse({'error': 'Missing parameters'}, status=400)

        pricing_options = PricingOption.objects.filter(
            service_id=service_id,
            customization_option_id__in=customization_ids
        ).values('id', 'description', 'price', 'customization_option_id')

        data = {}
        for option in pricing_options:
            cid = option['customization_option_id']
            if cid not in data:
                data[cid] = []
            data[cid].append({
                'id': option['id'],
                'description': option['description'],
                'price': str(option['price']),
            })
        print(data)

        return JsonResponse({'pricing_options': data}, status=200)
    return JsonResponse({'error': 'Invalid request'}, status=400)

from django.db.models import Q
def search_orders(request):
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        query = request.GET.get('query', '').strip()
        if query:
            # Filter orders by query (you can customize the fields being searched)
            search_results = Order.objects.filter(
                Q(service__name__icontains=query) | 
                Q(customer__name__icontains=query) |
                Q(status__icontains=query)
            )[:10]  # Limit results to 10

            html = render_to_string('includes/orders_search_results.html', {'orders': search_results})
            return JsonResponse({'html': html})
    
    return JsonResponse({'html': ''})

from django.shortcuts import render
from django.http import JsonResponse
from .models import Production, Inventory, Order
from .forms import ProductionForm
from django.views.decorators.csrf import csrf_exempt

# View for Production page
def production(request):
    orders = Order.objects.exclude(status__in=["CANCELLED", "COMPLETED"]).order_by('order_queue')
    materials = Inventory.objects.all()
    production_jobs = Production.objects.all()
    equipment_list = Equipment.objects.all()
    staff_list = User.objects.all()
    
    context = {
        'orders': orders,
        'materials': materials,
        'production_jobs': production_jobs,
        'equipment_list': equipment_list,
        'staff_list': staff_list,
    }
    return render(request, 'production.html', context)

import json
def submit_production(request):
    if request.method == 'POST':
        data = request.POST
        materials_data = request.POST.getlist('materials[]')  # Get materials as a list
        equipment_data = json.loads(request.POST.get('equipment_assigned', '[]'))
        quality_checks_data = json.loads(request.POST.get('quality_checks', '[]'))  # Fetch quality checks data if provided

        # Create a new Production instance
        production = Production(
            order_id=data.get('order'),  # Assuming `order` is passed as the ID
            equipment_assigned=equipment_data,
            status='IN_PROGRESS',  # Set the default status
            priority=data.get('priority', 'MODERATE'),  # Default priority if not provided
            quality_checks=quality_checks_data or [],  # Default to an empty list if not provided
        )
        production.save()

        # Add materials to the ManyToManyField
        if materials_data:
            materials = Inventory.objects.filter(pk__in=materials_data)  # Fetch Inventory objects
            production.materials.set(materials)  # Assign materials to Production

        order = Order.objects.get(order_id=data.get('order'))
        order.status = 'IN_PROGRESS'
        order.save()

        new_orders = Order.objects.filter(status='PENDING').order_by('order_queue')
        print(new_orders)
        sidebar = render_to_string('includes/orders_search_results.html', {'orders': new_orders})

        return JsonResponse({
            'sidebar': sidebar,
            'success': True,
            'operation_state': 'allowed',
            'message': f"Production job {production.job_id} created successfully!",
            'operation_name': 'Create Production',
            'name_color': 'green'
        })
    else:
        return JsonResponse({'success': False, 'error': 'Invalid request method'})



def fetch_materials(request):
    equipment_name = request.GET.get('equipment_name')
    if equipment_name:
        # Retrieve the selected equipment
        equipment = Equipment.objects.get(name=equipment_name)
        print(equipment)
        
        # Fetch all categories associated with the selected equipment
        categories = InventoryCategory.objects.filter(associated_equipment=equipment)
        print(categories)
        
        # Initialize a list to store the materials
        materials_list = []
        
        # Loop through each category and get related materials
        for category in categories:
            materials = category.get_related_inventory()  # This function fetches materials
            for material in materials:
                materials_list.append({
                    'id': material.material_id,
                    'name': material.name,
                })
        
        # Return the materials as JSON
        return JsonResponse({'materials': materials_list})
    return JsonResponse({'error': 'Equipment ID not provided'}, status=400)

def filter_by_priority(request):
    priority = request.GET.get('priority')
    
    # Ensure valid priority input
    if priority not in dict(Production.PRIORITY_CHOICES).keys():
        return JsonResponse({'error': 'Invalid priority value'}, status=400)

    # Filter based on the priority
    productions = Production.objects.filter(priority=priority)
    production_data = [{'job_id': p.job_id, 'priority': p.priority} for p in productions]
    return JsonResponse({'productions': production_data})

def filter_by_status(request):
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    productions = Production.objects.filter(status=status, priority=priority)
    production_data = [{'id': p.job_id, 'name': f'Job #{p.job_id} - {p.order.customer.name}'} for p in productions]
    return JsonResponse({'productions': production_data})

def fetch_quality_checks(request, production_id):
    # Fetch quality checks for the selected production
    production = Production.objects.get(job_id=production_id)
    quality_checks = production.quality_checks  # Assuming it's a JSONField
    print(quality_checks)
    return JsonResponse({"quality_checks": quality_checks, "job_id": production_id})

def get_quality_check(request, job_id, parameter):
    try:
        production = Production.objects.get(job_id=job_id)
        quality_checks = production.quality_checks 
        for check in quality_checks:
            if check.get('parameter') == parameter:
                return JsonResponse(check)
        return JsonResponse({'message': 'Quality check not found.'}, status=404)
    except Production.DoesNotExist:
        return JsonResponse({'message': 'Production not found.'}, status=404)

def save_quality_check(request, job_id, parameter):
    try:
        save_type = ''
        production = Production.objects.get(job_id=job_id)
        quality_checks = production.quality_checks 

        # Check if the quality check already exists
        for i, check in enumerate(quality_checks):
            if check['parameter'] == parameter:
                quality_checks[i] = {
                    'parameter': request.POST.get('parameter'),
                    'result': request.POST.get('result'),
                    'notes': request.POST.get('notes')
                }
                save_type = "Modified"
                break
        else:
            # If the quality check doesn't exist, create a new one
            quality_checks.append({
                'parameter': request.POST.get('parameter'),
                'result': request.POST.get('result'),
                'notes': request.POST.get('notes')
            })
            save_type = "Added"

        production.quality_checks = quality_checks
        production.save()

        production = Production.objects.get(job_id=job_id)
        quality_checks = production.quality_checks  # Assuming it's a JSONField

        return JsonResponse({"quality_checks": quality_checks, "job_id": job_id, "save_type": save_type})

    except Production.DoesNotExist:
        return JsonResponse({'message': 'Production not found.'}, status=404)


# AJAX view for updating production job status
@csrf_exempt
def update_production_status(request, job_id):
    if request.method == 'POST':
        status = request.POST.get('status')
        try:
            job = Production.objects.get(job_id=job_id)
            job.status = status
            job.save()
            return JsonResponse({'status': 'success', 'message': 'Production status updated successfully'})
        except Production.DoesNotExist:
            return JsonResponse({'status': 'error', 'message': 'Production job not found'})
    return JsonResponse({'status': 'error', 'message': 'Invalid request'})

# # Form to create or update production jobs
# def production_form(request):
#     if request.method == 'POST':
#         form = ProductionForm(request.POST)
#         if form.is_valid():
#             form.save()
#             return render(request, 'production/production_form_success.html')
#     else:
#         form = ProductionForm()
    
#     return render(request, 'production/production_form.html', {'form': form})

def search_production(request):
    query = request.GET.get("q", "")
    results = Production.objects.filter(job_id__icontains=query) if query else []
    return render(request, "includes/production/search_results.html", {"results": results})

def inventory_management(request):
    categories = InventoryCategory.objects.all()
    organized_inventory = {}

    for category in categories:
        # Get the related inventory items for each category
        inventory_items = category.get_related_inventory()

        # Organize inventory items by category
        organized_inventory[category.category_name] = [
            {
                "name": item.name,
                "stock_level": item.stock_level,
                "reorder_threshold": item.reorder_threshold,
                "unit": item.get_unit_of_measurement_display(),
                "supplier": {
                    "name": item.supplier.supplier_name if item.supplier else "No Supplier",
                    "contact": item.supplier.contact_person if item.supplier else "N/A",
                    "phone": item.supplier.phone_number if item.supplier else "N/A",
                    "email": item.supplier.email if item.supplier else "N/A",
                    "address": item.supplier.address if item.supplier else "N/A",
                }
            }
            for item in inventory_items
        ]

    return render(request, "includes/production/production_inventory.html", {"inventory": organized_inventory})

from django.db.models import F
def inventory_alerts(request):
    alerts = Inventory.objects.filter(stock_level__lt=F('reorder_threshold'))
    return render(request, "includes/production/production_alert_inventory.html", {"alerts": alerts})

@csrf_exempt
def contact_supplier(request):
    if request.method == "POST":
        supplier_name = request.POST.get("supplier_name")
        material_name = request.POST.get("material_name")
        message = request.POST.get("message")
        # Add logic to send email or store the message
        return JsonResponse({"status": "success", "message": "Message sent successfully"})
    return JsonResponse({"status": "error", "message": "Invalid request"})


def crm_view(request):
    customers = Customer.objects.all()  # Fetch all customers
    return render(request, 'crm.html', {'customers': customers})

# PAYMENT VIEWS
def payment(request):
   return render(request, "payment.html")

from django.shortcuts import render, redirect
from django.http import JsonResponse
from .models import Order, Payment
from .forms import PaymentForm

def new_payment(request):
    if request.method == 'POST':
        form = PaymentForm(request.POST)
        
        if form.is_valid():
            order_id = form.cleaned_data['order']
            amount = form.cleaned_data['amount']
            payment_method = form.cleaned_data['payment_method']
            status = form.cleaned_data['status']
            payment_date = form.cleaned_data['payment_date']

            # Retrieve the order object
            order = Order.objects.get(id=order_id)

            # Create the payment record
            payment = Payment.objects.create(
                order=order,
                amount=amount,
                payment_method=payment_method,
                status=status,
                payment_date=payment_date
            )

            # Update the order status if fully paid
            if status == 'PAID' and order.total_amount == amount:
                order.status = 'PAID'
                order.save()

            # Redirect or respond with success message
            return redirect('payment_history')  # Redirect to payment history page
        
        else:
            return render(request, 'payments/new_payment.html', {'form': form})
    
    else:
        form = PaymentForm()
    
    return render(request, 'payments/new_payment.html', {'form': form})


def estimatesv2(request):
   return render(request, "estimates2.html")
