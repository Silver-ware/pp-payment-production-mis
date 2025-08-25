import factory
from factory import SubFactory, post_generation
from faker import Faker
from django.utils.timezone import now
from decimal import Decimal
from .models import (
    Customer, Service, CustomizationOption, Order, Payment, PricingOption,
    Inventory, InventoryCategory, Supplier, Equipment, Production, PaymentMethod
)
import random
from datetime import datetime
from django.utils.timezone import make_aware

faker = Faker()

class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    name = factory.Faker('name')
    contact_number = factory.Faker('phone_number')
    email = factory.Faker('email')
    address = factory.Faker('address')


class CustomizationOptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomizationOption

    name = factory.LazyAttribute(lambda x: faker.unique.word())


class ServiceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Service

    name = factory.Faker('company')

    @post_generation
    def customization_options(self, create, extracted, **kwargs):
        if not create:

            return

        options = CustomizationOption.objects.all()
        selected_options = random.sample(list(options), random.randint(2, 5))
        self.customization_options.set(selected_options)
        print("Service created!")



class PricingOptionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PricingOption

    customization_option = factory.SubFactory(CustomizationOptionFactory)
    service = factory.SubFactory(ServiceFactory)
    description = factory.Faker('sentence', nb_words=6)
    price = factory.LazyAttribute(lambda _: faker.pydecimal(left_digits=4, right_digits=2, positive=True))

    @classmethod
    def create_for_service(cls, service):
        for customization_option in service.customization_options.all():
            num_pricing_options = random.randint(1, 3)
            for _ in range(num_pricing_options):
                option = cls.create(
                    service=service,
                    customization_option=customization_option,
                    price=faker.pydecimal(left_digits=4, right_digits=2, positive=True)
                )



class PaymentMethodFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = PaymentMethod

    method_name = factory.LazyAttribute(lambda x: faker.unique.word())

import random
from datetime import datetime
from django.db import models
from django.utils.timezone import make_aware
import factory
from factory.django import DjangoModelFactory
from system.models import Order


class OrderFactory(DjangoModelFactory):
    class Meta:
        model = Order

    customer = factory.SubFactory('system.factories.CustomerFactory')
    service = factory.LazyFunction(lambda: random.choice(Service.objects.all()))  
    job_specifications = factory.LazyFunction(
        lambda: {
            "jobs_specifications": [
                {
                    "specification": faker.word(),
                    "details": faker.sentence(),
                }
                for _ in range(random.randint(1, 5))
            ]
        }
    )
    status = factory.Iterator(['PENDING', 'IN PROGRESS', 'COMPLETED', 'CANCELLED'])
    order_queue = None
    deadline = factory.Faker('future_datetime', end_date='+30d')
    completed_or_cancelled = None
    payment = None

    @factory.post_generation
    def set_fields(obj, create, extracted, **kwargs):
        
        if not create:
            return

        if obj.status in ['COMPLETED', 'CANCELLED']:

            obj.completed_or_cancelled = make_aware(datetime.now())
            obj.order_queue = None 
        else:

            max_queue = Order.objects.filter(status__in=['PENDING', 'IN PROGRESS']).aggregate(max_queue=models.Max('order_queue'))['max_queue']

            obj.order_queue = (max_queue or 0) + 1
            obj.completed_or_cancelled = None 

        obj.save()

    

class PaymentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Payment

    order = factory.SubFactory(OrderFactory)
    amount = factory.Faker('pydecimal', left_digits=3, right_digits=2, positive=True)
    amount_paid = factory.LazyAttribute(lambda obj: obj.amount * Decimal(random.uniform(0.5, 1.0)))
    payment_method = factory.SubFactory(PaymentMethodFactory)
    status = factory.Iterator(['PENDING', 'PARTIALLY_PAID', 'PAID'])


class EquipmentFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Equipment

    name = factory.Faker('word')
    description = factory.Faker('sentence')
    condition = factory.Iterator(['new', 'working', 'damaged', 'broken'])

class InventoryCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = InventoryCategory

    category_name = factory.LazyAttribute(lambda x: faker.unique.word())

    @factory.post_generation
    def associated_equipment(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:

            self.associated_equipment.set(extracted)
        else:
            equipments = Equipment.objects.all()
            selected_equipment = random.sample(list(equipments), random.randint(2, 5))
            self.associated_equipment.set(selected_equipment)




class SupplierFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Supplier

    supplier_name = factory.Faker('company')
    contact_person = factory.Faker('name')
    phone_number = factory.Faker('phone_number')
    email = factory.Faker('email')
    address = factory.Faker('address')


class InventoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Inventory

    name = factory.Faker('word')
    category = factory.SubFactory(InventoryCategoryFactory)
    stock_level = factory.Faker('random_int', min=10, max=1000)
    reorder_threshold = factory.Faker('random_int', min=5, max=50)
    supplier = factory.SubFactory(SupplierFactory)
    unit_of_measurement = factory.Iterator(['qty', 'kg', 'pcs', 'liters', 'sheets'])

class ProductionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Production

    order = factory.SubFactory(OrderFactory)
    status = factory.LazyAttribute(lambda obj: obj.order.status if obj.order.status in ['COMPLETED', 'CANCELLED'] else random.choice(['IN_PROGRESS', 'ON_HOLD']))
    priority = factory.Iterator(['HIGH', 'MODERATE', 'LOW'])

    @factory.post_generation
    def materials(self, create, extracted, **kwargs):
        if not create:
            return
        if extracted:
            self.materials.add(*extracted)
        else:

            self.materials.add(*Inventory.objects.order_by("?")[:3])

    @factory.lazy_attribute
    def equipment_assigned(self):

        return [{"equipment_id": eq.equipment_id} for eq in Equipment.objects.order_by("?")[:2]]

    @factory.lazy_attribute
    def quality_checks(self):

        num_checks = random.randint(2, 5)
        if self.status == "COMPLETED":
            return [
                {
                    "parameter": f"Parameter {i+1}",
                    "result": "pass",
                    "notes": "All checks passed successfully."
                }
                for i in range(num_checks)
            ]
        else:
            return [
                {
                    "parameter": f"Parameter {i+1}",
                    "result": random.choice(["pass", "fail"]),
                    "notes": "Matched with original design" if i % 2 == 0 else "Needs adjustment"
                }
                for i in range(num_checks)
            ]

