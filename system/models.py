from django.db import models
import json
from decimal import Decimal
from django.utils.timezone import make_aware

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    contact_number = models.CharField(max_length=255)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)

    def __str__(self):
        return self.name
    
    def get_order_history(self):
        return self.orders.all()  # Using the related_name

    def get_payment_history(self):
        return Payment.objects.filter(order__customer=self)  # Filter payments by customer's orders
    
class Service(models.Model):
    service_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    customization_options = models.ManyToManyField(
        'CustomizationOption', related_name="services", blank=True
    )

    def __str__(self):
        return self.name

    def get_pricing_options_by_customization(self):
        """
        Organize pricing options by their respective customization options.

        Returns:
            dict: A dictionary where keys are customization options, and values are lists of pricing options.
        """
        pricing_options = self.pricing_options.select_related('customization_option')
        organized_options = {}

        for pricing_option in pricing_options:
            customization = pricing_option.customization_option
            if customization not in organized_options:
                organized_options[customization] = []
            organized_options[customization].append(pricing_option)

        return organized_options



class CustomizationOption(models.Model):
    name = models.CharField(max_length=255, unique=True)

    def __str__(self):
        return self.name


class PricingOption(models.Model):
    service = models.ForeignKey(
        'Service', on_delete=models.CASCADE, related_name='pricing_options'
    )
    customization_option = models.ForeignKey(
        'CustomizationOption', on_delete=models.CASCADE, related_name='pricing_options'
    )
    description = models.CharField(max_length=255)  # e.g., "Bond Paper - Non-colored: 3 pesos"
    price = models.DecimalField(max_digits=10, decimal_places=2)  # Actual price value

    def __str__(self):
        return f"{self.service.name} - {self.customization_option.name}: {self.description} (Price: {self.price} pesos)"

def decimal_to_float(obj):
    """Helper function to convert Decimal to float for JSON serialization."""
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Object of type {obj.__class__.__name__} is not JSON serializable")

class Order(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('IN PROGRESS', 'In Progress'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
    ]

    order_id = models.AutoField(primary_key=True)
    order_queue = models.IntegerField(blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, related_name='orders')
    service = models.ForeignKey(Service, on_delete=models.CASCADE, related_name='orders')
    job_specifications = models.JSONField(null=True, blank=True) # Paper size (e.g., "A4", "A3", "Legal", "Letter")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    deadline = models.DateTimeField()
    payment = models.ForeignKey('Payment', null=True, blank=True, on_delete=models.SET_NULL, related_name='orders')
    created_at = models.DateTimeField(auto_now_add=True)
    completed_or_cancelled = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        # Ensure job_specifications are JSON-serializable
        if isinstance(self.job_specifications, dict):
            self.job_specifications = json.loads(
                json.dumps(self.job_specifications, default=decimal_to_float)
            )
        # Ensure deadline is timezone-aware
        if self.deadline and self.deadline.tzinfo is None:
            self.deadline = make_aware(self.deadline)
        super().save(*args, **kwargs)
        # Ensure completed_or_cancelled is timezone-aware
        if self.completed_or_cancelled and self.completed_or_cancelled.tzinfo is None:
            self.completed_or_cancelled = make_aware(self.completed_or_cancelled)

    def __str__(self):
        return f"Order {self.order_id} - {self.customer.name}"
    
class Payment(models.Model):
    PAYMENT_STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PARTIALLY_PAID', 'Partially Paid'),
        ('PAID', 'Paid'),
        ('FAILED', 'Failed'),
        ('REFUNDED', 'Refunded'),
    ]

    DISCOUNT_TYPE_CHOICES = [
        ('fixed', 'Fixed Amount'),       # E.g., 50 pesos off
        ('percentage', 'Percentage'),   # E.g., 10% off
    ]

    payment_id = models.AutoField(primary_key=True)
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)  # Original payment amount
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # Amount actually paid
    payment_method = models.ForeignKey(
        "PaymentMethod", on_delete=models.SET_NULL, null=True, blank=True, related_name='payments'
    )
    discount = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True, default=0.00
    )  # Discount value (amount or percentage)
    discount_type = models.CharField(
        max_length=10, choices=DISCOUNT_TYPE_CHOICES, null=True, blank=True
    )  # 'fixed' or 'percentage'
    discount_name = models.CharField(
        max_length=100, null=True, blank=True, default="", help_text="Name or type of the discount"
    )  # e.g., "PWD Discount", "Seasonal Sale"
    status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='PENDING')
    payment_date = models.DateTimeField(auto_now_add=True)

    def get_final_price(self):
        """Calculate the final price after applying the discount."""
        if self.discount_type == 'percentage':
            discount_amount = (self.discount / 100) * self.amount
        elif self.discount_type == 'fixed':
            discount_amount = self.discount
        else:
            discount_amount = 0

        # Ensure final price is not negative
        return max(self.amount - discount_amount, 0)

    def __str__(self):
        final_price = self.get_final_price()
        discount_info = f", Discount: {self.discount_name}" if self.discount_name else ""
        return (
            f"Payment {self.payment_id} for Order {self.order.order_id} "
            f"(Original: {self.amount} pesos, Final: {final_price} pesos{discount_info})"
        )

class PaymentMethod(models.Model):
    method_name = models.CharField(max_length=50, unique=True)  # e.g., 'Cash', 'Credit Card'
    details = models.TextField(null=True, blank=True)  # Optional details, like account info or instructions

    def __str__(self):
        return self.method_name

from django.db import models

class Equipment(models.Model):
    equipment_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    description = models.TextField(null=True, blank=True)
    condition = models.CharField(
        max_length=50,
        choices=[('new', 'New'), ('working', 'Working'), ('damaged', 'Damaged'), ('broken', 'Broken')]
    )

    def __str__(self):
        return self.name


class InventoryCategory(models.Model):
    category_name = models.CharField(max_length=100, unique=True)
    associated_equipment = models.ManyToManyField(
        Equipment,
        blank=True,
        related_name="categories"
    )

    def __str__(self):
        return self.category_name

    def get_related_inventory(self):
        """
        Retrieves all Inventory instances that belong to this category.
        """
        return self.materials.all()  # 'materials' comes from the `related_name` in the Inventory model.


class Inventory(models.Model):
    UNIT_CHOICES = [
        ("qty", "qty"),
        ("liters", "liters"),
        ("meters", "meters"),
        ("mm", "mm"),
        ("rolls", "rolls"),
        ("sheets", "sheets"),
        ("kg", "kg"),
        ("pcs", "pcs"),
        ("cm", "cm"),
        ("grams", "grams"), 
    ]

    material_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(
        InventoryCategory, on_delete=models.SET_NULL, null=True, related_name='materials'
    )
    stock_level = models.IntegerField()
    reorder_threshold = models.IntegerField()
    supplier = models.ForeignKey(
        "Supplier", on_delete=models.SET_NULL, null=True, related_name='supplies'
    )
    unit_of_measurement = models.CharField(
        max_length=20,
        choices=UNIT_CHOICES,
        default="qty",
    )

    def __str__(self):
        return self.name

class Production(models.Model):
    PRIORITY_CHOICES = [
        ('HIGH', 'High'),
        ('MODERATE', 'Moderate'),
        ('LOW', 'Low'),
    ]

    job_id = models.AutoField(primary_key=True)
    order = models.ForeignKey("Order", on_delete=models.CASCADE, related_name="productions")
    materials = models.ManyToManyField("Inventory", related_name="productions")
    equipment_assigned = models.JSONField()
    quality_checks = models.JSONField()
    status = models.CharField(
        max_length=50,
        choices=[
            ('IN_PROGRESS', 'In Progress'),
            ('ON_HOLD', 'On Hold'),
            ('COMPLETED', 'Completed'),
            ('CANCELLED', 'Cancelled'),
        ],
        default='NOT_STARTED'
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='MODERATE'
    )

    def __str__(self):
        return f"Production Job {self.job_id} - {self.get_status_display()}"

    
class Supplier(models.Model):
    supplier_name = models.CharField(max_length=255)
    contact_person = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    additional_info = models.TextField(null=True, blank=True)  # Any extra details

    def __str__(self):
        return self.supplier_name

class BusinessDetails(models.Model):
    name = models.CharField(max_length=255, help_text="Name of the business or organization.")
    address = models.TextField(help_text="Complete address of the business.")
    contact_number = models.CharField(max_length=15, blank=True, null=True, help_text="Business contact number.")
    email = models.EmailField(blank=True, null=True, help_text="Business email address.")
    tax_identification_number = models.CharField(max_length=50, blank=True, null=True, help_text="Tax ID or equivalent.")
    logo = models.ImageField(upload_to='business_logos/', blank=True, null=True, help_text="Upload the business logo.")

    def __str__(self):
        return self.name

class SystemSettings(models.Model):
    currency = models.CharField(max_length=10, default='USD', help_text="Default currency for transactions.")
    timezone = models.CharField(max_length=50, default='UTC', help_text="System default timezone.")
    date_format = models.CharField(max_length=20, default='YYYY-MM-DD', help_text="Default format for dates.")
    language = models.CharField(max_length=20, default='en', help_text="Default language for the system.")
    smtp_server = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP server address.")
    smtp_port = models.PositiveIntegerField(blank=True, null=True, help_text="SMTP port number.")
    smtp_email = models.EmailField(blank=True, null=True, help_text="SMTP email address.")
    smtp_password = models.CharField(max_length=255, blank=True, null=True, help_text="SMTP email password.")

    def __str__(self):
        return "System Settings"

class AuditLog(models.Model):
    action = models.CharField(max_length=255, help_text="Description of the action performed.")
    timestamp = models.DateTimeField(auto_now_add=True, help_text="Time when the action occurred.")
    user = models.ForeignKey('auth.User', on_delete=models.SET_NULL, null=True, blank=True, help_text="User who performed the action.")

    def __str__(self):
        return f"{self.action} at {self.timestamp}"
    
