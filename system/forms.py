import json, re
from django.utils.timezone import now
from django import forms  
from django.contrib.auth.models import User, Group  
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from .models import Service, PricingOption, BusinessDetails, Equipment, Inventory, Supplier, Customer, SystemSettings, Order, Production


class SuperuserAuthenticationForm(forms.Form):
    username = forms.CharField(label="Superuser Username", max_length=150)
    password = forms.CharField(label="Password", widget=forms.PasswordInput)

class BusinessDetailsForm(forms.Form):
    class Meta:
        model = BusinessDetails
        fields = ['name', 'address', 'contact_number', 'email', 'tax_identification_number', 'logo']

    business_name = forms.CharField(
        max_length=255,
        required=True,
    )
    business_address = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 3,
        }),
        required=True,
    )
    contact_number = forms.RegexField(
        regex=r'^\+?1?\d{9,15}$',
        required=False,
        error_messages={
            'invalid': 'Enter a valid contact number (9-15 digits, optional country code).',
        },
    )
    email = forms.EmailField(
        required=False,
    )
    tin = forms.CharField(
        max_length=20,
        required=False,
    )
    logo = forms.ImageField(
        required=False,
    )

    def clean_business_name(self):
        business_name = self.cleaned_data.get('business_name')
        if not all(char.isalnum() or char.isspace() for char in business_name):
            raise forms.ValidationError("Business name should only contain letters and numbers.")
        return business_name

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if email and not email.endswith('@example.com'):
            raise forms.ValidationError("Email address must end with @example.com.")
        return email
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if contact_number:
            if len(contact_number) < 11:
                raise forms.ValidationError("Phone number must be at least 11 digits.")
        return contact_number

    def clean_tin(self):
        tin = self.cleaned_data.get('tin')
        print(tin)
        if tin:
            if not tin.isdigit():
                raise forms.ValidationError("Tax Identification Number (TIN) must contain only numbers.")
            if len(tin) < 9 or len(tin) > 20:
                raise forms.ValidationError("TIN must be between 9 and 20 digits.")



            return tin

    def clean_logo(self):
        logo = self.cleaned_data.get('logo')
        if logo:

            max_file_size = 2 * 1024 * 1024  # 2MB
            if logo.size > max_file_size:
                raise forms.ValidationError("Logo file size must not exceed 2MB.")

            valid_mime_types = ["image/jpeg", "image/png"]
            if logo.content_type not in valid_mime_types:
                raise forms.ValidationError("Logo must be a JPEG or PNG image.")

            from PIL import Image
            try:
                image = Image.open(logo)
                max_width, max_height = 1024, 1024
                if image.width > max_width or image.height > max_height:
                    raise forms.ValidationError(f"Logo dimensions must not exceed {max_width}x{max_height} pixels.")
            except Exception:
                raise forms.ValidationError("Uploaded file is not a valid image.")

    def clean(self):
        cleaned_data = super().clean()
        business_name = cleaned_data.get('business_name')
        business_address = cleaned_data.get('business_address')

        if business_name and business_address:
            if "Test" in business_name and "Test" in business_address:
                raise forms.ValidationError("Business name and address cannot both contain 'Test'.")
        return cleaned_data

class ServiceForm(forms.ModelForm):
    customization_options = forms.CharField(
        required=False,
        widget=forms.TextInput(),  
    )
    class Meta:
        model = Service
        fields = ['name', 'customization_options']

    def clean_customization_options(self):
        options = self.cleaned_data.get('customization_options')
        print(f"Received customization options: {options}")
        if options:
            try:

                options_list = json.loads(options)
                if not isinstance(options_list, list):
                    raise ValueError
                if not all(isinstance(option, str) and option.strip() for option in options_list):
                    raise ValueError
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid customization options format. Please use valid text tags.")
            
            if len(options_list) > 10:  
                raise forms.ValidationError("You can add a maximum of 10 customization options.")
            
            return options_list
        return []
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError("Service name must be at least 3 characters long.")
        return name



class PricingOptionForm(forms.ModelForm):
    class Meta:
        model = PricingOption
        fields = ['customization_option', 'description', 'price']
        widgets = {
            'customization_option': forms.Select(),
        }

class EquipmentForm(forms.Form):
    class Meta:
        model = Equipment
        fields = ['name', 'description', 'condition']
    name = forms.CharField(
        max_length=255,
        required=True,
        widget=forms.TextInput(attrs={'class': 'custom-input'})
    )
    description = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 4, 'class': 'custom-textarea'}),
        required=True
    )
    condition = forms.ChoiceField(
        choices=[('new', 'New'), ('working', 'Working'), ('damaged', 'Damaged'), ('broken', 'Broken')],
        widget=forms.Select(attrs={'class': 'custom-select'}),
        required=True
    )

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 3:
            raise forms.ValidationError("Equipment name must have at least 3 characters.")
        return name


class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['name', 'stock_level', 'reorder_threshold', 'unit_of_measurement']

    category = forms.CharField(
        max_length=255,
        widget=forms.TextInput(attrs={'placeholder': 'Select or type a category'}),
    )
    supplier = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': 'Enter supplier name'}),
    )
    unit_of_measurement = forms.ChoiceField(
        choices=Inventory.UNIT_CHOICES,
        widget=forms.Select(attrs={'class': 'w-full mt-1 p-3 border rounded-lg focus:ring-green-500 focus:border-green-500'}),
    )

    def clean_category(self):

        category = self.cleaned_data['category']
        predefined_categories = ["Ink", "Textiles", "Vinyl", "Paper", "Adhesives", "Fabrics", "Other"]
        if category not in predefined_categories:
            raise forms.ValidationError("Invalid category selected.")
        return category

    def clean_supplier(self):

        supplier = self.cleaned_data['supplier']
        return supplier  # No strict validation for now
    
    def clean_stock_level(self):
        stock_level = self.cleaned_data.get('stock_level')
        if stock_level < 0:
            raise forms.ValidationError("Stock level cannot be negative.")
        return stock_level

    def clean_reorder_threshold(self):
        reorder_threshold = self.cleaned_data.get('reorder_threshold')
        if reorder_threshold < 0:
            raise forms.ValidationError("Reorder threshold cannot be negative.")
        return reorder_threshold
    
    def clean(self):
        cleaned_data = super().clean()

        return cleaned_data

class SupplierForm(forms.ModelForm):
    class Meta:
        model = Supplier
        fields = ['supplier_name', 'contact_person', 'phone_number', 'email', 'address', 'additional_info']

    def clean_phone_number(self):
        phone_number = self.cleaned_data.get('phone_number')
        if phone_number:

            if len(phone_number) < 11:
                raise forms.ValidationError("Phone number must be at least 10 digits.")
        return phone_number

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA10-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise ValidationError("Invalid email format.")
        return email


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['name', 'contact_number', 'email', 'address']

    def clean_name(self):
        name = self.cleaned_data.get('name')
        if len(name) < 5:
            raise ValidationError("Full name must be at least 5 characters long.")
        return name
    
    def clean_contact_number(self):
        contact_number = self.cleaned_data.get('contact_number')
        if not re.match(r'^\+?[0-9]{10,15}$', contact_number):
            raise ValidationError("Invalid contact number. Ensure it contains only numbers and is between 10-15 digits.")
        return contact_number
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if not re.match(r'^[a-zA-Z0-9_.+-]+@[a-zA10-9-]+\.[a-zA-Z0-9-.]+$', email):
            raise ValidationError("Invalid email format.")
        return email


class SystemSettingsForm(forms.ModelForm):
    class Meta:
        model = SystemSettings
        fields = ['smtp_server', 'smtp_port', 'smtp_email', 'smtp_password']

    smtp_port = forms.IntegerField(
        required=True,
        label="SMTP Port",
        help_text="Use 465 (SSL) or 587 (TLS) for Google.",
    )
    smtp_email = forms.EmailField(
        required=True,
        label="SMTP Email",
        help_text="Must be a valid Gmail address (e.g., user@gmail.com).",
    )
    smtp_password = forms.CharField(
        required=True,
        widget=forms.PasswordInput,
        label="SMTP Password",
        help_text="Enter a 16-character App Password generated by Google.",
    )

    def clean_smtp_port(self):
        port = self.cleaned_data.get('smtp_port')
        if port not in [465, 587]:
            raise ValidationError("Invalid SMTP port. Use 465 (SSL) or 587 (TLS) for Google.")
        return port

    def clean_smtp_email(self):
        email = self.cleaned_data.get('smtp_email')
        if not email.endswith('@gmail.com'):
            raise ValidationError("The SMTP email must be a Gmail address (e.g., user@gmail.com).")
        return email

    def clean_smtp_password(self):
        password = self.cleaned_data.get('smtp_password')
        if len(password) != 16:
            raise ValidationError("Invalid SMTP password. Ensure it's a 16-character App Password generated by Google.")
        return password


class CustomUserCreationForm(UserCreationForm):  
    username = forms.CharField(
        label='username', 
        min_length=5, 
        max_length=150,
        error_messages={
            'required': 'Please enter a username.',
            'min_length': 'Enter atleast 5 characters.',
        }
    )
    password1 = forms.CharField(
        label='password', widget=forms.PasswordInput,
        error_messages={
            'required': 'Password is required.'
        }    
    )  
    password2 = forms.CharField(
        label='Confirm password', widget=forms.PasswordInput,
        error_messages={
            'required': 'Re-enter the password correctly.'
        }
    )  
    email = forms.EmailField(
        error_messages={
            'required': 'Enter a working email.'
        }
    )
    first_name = forms.CharField(
        error_messages={
            'required': 'Enter a first name:'
        }
    )
    last_name = forms.CharField(
        error_messages={
            'required': 'Enter a last name:'
        }
    )
    role = forms.ChoiceField(
        choices=[
            ("Managerial", "Managerial"),
            ("Artist/Designer", "Artist/Designer"),
            ("Staff/Clerk", "Staff/Clerk"),
            ("Others", "Others"),
        ],
        required=True
    )
    
    def clean_username(self):  
        username = self.cleaned_data['username'].lower()  
        new = User.objects.filter(username = username)  
        if new.count():  
            raise ValidationError("User Already Exist")  
        return username   
  
    def clean_password2(self):  
        password1 = self.cleaned_data['password1']  
        password2 = self.cleaned_data['password2']  
  
        if password1 and password2 and password1 != password2:  
            raise ValidationError("Password don't match!")  
        return password2  
  
    def clean_email(self):
        email = self.cleaned_data['email']
        if not email.endswith('@gmail.com'):
            raise forms.ValidationError("Only google email are allowed.")
        return email


    def save(self, view_name=None):   
        is_staff = False
        is_active = True
        is_superuser = False

        if view_name == "admin_signup": 
            is_staff = True
            is_active = True
            is_superuser = True
            groups = "Administrator"
        else:
            role_settings = {
                "Managerial": {"is_staff": True, "is_active": True, "is_superuser": True, "groups": "Administrator" },
                "Staff/Clerk": {"is_staff": True, "is_active": True, "is_superuser": False, "groups": "Staff or Clerk" },
                "Artist/Designer": {"is_staff": False, "is_active": True, "is_superuser": False, "groups": "Artist or Designer"},
                "Others": {"is_staff": False, "is_active": True, "is_superuser": False, "groups": "Other"},
            }

            role = self.cleaned_data.get('role', "Others")
            settings = role_settings.get(role, {"is_staff": False, "is_active": True, "is_superuser": False})

            is_staff = settings["is_staff"]
            is_active = settings["is_active"]
            is_superuser = settings["is_superuser"]
            groups = settings["groups"]

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            password=self.cleaned_data['password2'],
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            email=self.cleaned_data['email'],
        )

        user.is_staff = is_staff
        user.is_active = is_active
        user.is_superuser = is_superuser

        if groups:
            group, created = Group.objects.get_or_create(name=groups)
            user.groups.add(group)

        user.save()
        return user

class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['service', 'job_specifications', 'deadline']

    def clean_deadline(self):
        deadline = self.cleaned_data['deadline']
        if deadline <= now():
            raise forms.ValidationError("Deadline must be in the future.")
        return deadline


class ProductionForm(forms.ModelForm):
    class Meta:
        model = Production
        fields = ['order', 'materials', 'equipment_assigned', 'quality_checks', 'status']

    materials = forms.ModelMultipleChoiceField(
        queryset=Inventory.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
    )
    equipment_assigned = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter equipment details'}),
        required=False,
    )
    quality_checks = forms.CharField(
        widget=forms.Textarea(attrs={'placeholder': 'Enter quality check details'}),
        required=False,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


from .models import Payment
class PaymentForm(forms.Form):
    order = forms.ModelChoiceField(queryset=Order.objects.all(), required=True)
    amount = forms.DecimalField(max_digits=10, decimal_places=2, required=True)
    status = forms.ChoiceField(choices=Payment.PAYMENT_STATUS_CHOICES, required=True)
    payment_date = forms.DateField(widget=forms.SelectDateWidget, required=True)

