import random
from django.core.management.base import BaseCommand
from system.factories import (
    CustomerFactory, CustomizationOptionFactory, ServiceFactory, PricingOptionFactory,
    PaymentMethodFactory, PaymentFactory, OrderFactory, InventoryCategoryFactory,
    SupplierFactory, InventoryFactory, EquipmentFactory, ProductionFactory
)
from system.models import Equipment

class Command(BaseCommand):
    help = "Seed the database with example data"

    def handle(self, *args, **kwargs):
        try:
            # Customers
            customers = CustomerFactory.create_batch(10)
            self.stdout.write(self.style.SUCCESS(f"Created {len(customers)} customers"))

            # Customization Options
            customization_options = CustomizationOptionFactory.create_batch(15)
            self.stdout.write(self.style.SUCCESS(f"Created {len(customization_options)} customization options"))

            # Services
            services = ServiceFactory.create_batch(20)
            for service in services:
                num_customization_options = random.randint(2, 5)
                linked_options = random.sample(customization_options, num_customization_options)
                service.customization_options.set(linked_options)
            self.stdout.write(self.style.SUCCESS(f"Created {len(services)} services"))

            # Pricing Options
            total_pricing_options = 0
            for service in services:
                try:
                    num_options_before = PricingOptionFactory._meta.model.objects.filter(service=service).count()
                    PricingOptionFactory.create_for_service(service)
                    num_options_after = PricingOptionFactory._meta.model.objects.filter(service=service).count()
                    total_pricing_options += (num_options_after - num_options_before)
                except Exception as e:
                    print(f"Error creating pricing options for service {service.name}: {e}")
            self.stdout.write(self.style.SUCCESS(f"Created {total_pricing_options} pricing options"))

            # Payment Methods
            payment_methods = PaymentMethodFactory.create_batch(5)
            self.stdout.write(self.style.SUCCESS(f"Created {len(payment_methods)} payment methods"))

            # Seeding Orders without payment
            orders = []
            for _ in range(75):
                order = OrderFactory(status=random.choice(['PENDING', 'IN PROGRESS', 'COMPLETED', 'CANCELLED']))
                orders.append(order)
            self.stdout.write(self.style.SUCCESS(f"Created {len(orders)} orders"))

            # Seeding Payments and linking to existing Orders
            for order in orders[:25]:
                payment = PaymentFactory(order=order)
                order.payment = payment
                order.save()
            self.stdout.write(self.style.SUCCESS(f"Created 25 payments and linked to orders"))

            # Suppliers
            suppliers = SupplierFactory.create_batch(5)
            self.stdout.write(self.style.SUCCESS(f"Created {len(suppliers)} suppliers"))

            # Equipment
            equipment = EquipmentFactory.create_batch(20)
            self.stdout.write(self.style.SUCCESS(f"Created {len(equipment)} equipment"))

            # Create 10 categories, each with 2 to 5 associated equipment items
            categories = []
            for _ in range(10):
                category = InventoryCategoryFactory.create()  # Create the category first
                num_equipment = random.randint(2, 5)  # Randomly decide how many equipment items to associate
                
                # Ensure that we don't sample more equipment than are available
                available_equipment = list(Equipment.objects.all())
                if len(available_equipment) < num_equipment:
                    num_equipment = len(available_equipment)  # Adjust if not enough equipment
                
                selected_equipment = random.sample(available_equipment, num_equipment)  # Select equipment items randomly
                category.associated_equipment.set(selected_equipment)  # Link the selected equipment to the category
                categories.append(category)

            self.stdout.write(self.style.SUCCESS(f"Created {len(categories)} inventory categories"))

            # Inventory
            inventories = []
            for _ in range(35):
                inventory = InventoryFactory(category=random.choice(categories))  # Assign category from the created ones
                inventories.append(inventory)
            self.stdout.write(self.style.SUCCESS(f"Created {len(inventories)} inventory items"))

            # Production Jobs - Only for orders in IN PROGRESS
            productions = []
            for order in orders:
                # Create production jobs based on the order status
                production = ProductionFactory(order=order, materials=inventories[:5])  # Link materials if needed
                productions.append(production)

            self.stdout.write(self.style.SUCCESS(f"Created {len(productions)} production jobs"))


        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error occurred: {str(e)}"))
