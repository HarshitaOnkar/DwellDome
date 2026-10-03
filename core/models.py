from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class Home(models.Model):
    owner = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='home'
    )

    name = models.CharField(
        max_length=100,
        default='My Home'
    )

    address = models.TextField(
        blank=True
    )

    warranty_reminders_enabled = models.BooleanField(
        default=True
    )

    maintenance_reminders_enabled = models.BooleanField(
        default=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name


class Room(models.Model):

    ROOM_TYPES = [
        ('living_room', 'Living Room'),
        ('bedroom', 'Bedroom'),
        ('kitchen', 'Kitchen'),
        ('bathroom', 'Bathroom'),
        ('dining_room', 'Dining Room'),
        ('office', 'Office'),
        ('balcony', 'Balcony'),
        ('other', 'Other'),
    ]

    home = models.ForeignKey(
        Home,
        on_delete=models.CASCADE,
        related_name='rooms'
    )

    name = models.CharField(
        max_length=100
    )

    room_type = models.CharField(
        max_length=30,
        choices=ROOM_TYPES,
        default='other'
    )

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name
    
    
class Asset(models.Model):

    CATEGORY_CHOICES = [
        ('appliance', 'Appliance'),
        ('electronics', 'Electronics'),
        ('furniture', 'Furniture'),
        ('gadget', 'Gadget'),
        ('kitchen', 'Kitchen'),
        ('decor', 'Decor'),
        ('other', 'Other'),
    ]

    CONDITION_CHOICES = [
        ('new', 'New'),
        ('good', 'Good'),
        ('fair', 'Fair'),
        ('needs_repair', 'Needs Repair'),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.CASCADE,
        related_name='assets'
    )

    name = models.CharField(
        max_length=150
    )

    category = models.CharField(
        max_length=30,
        choices=CATEGORY_CHOICES,
        default='other'
    )

    brand = models.CharField(
        max_length=100,
        blank=True
    )

    model_number = models.CharField(
        max_length=100,
        blank=True
    )

    serial_number = models.CharField(
        max_length=100,
        blank=True
    )

    purchase_date = models.DateField(
        null=True,
        blank=True
    )

    purchase_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )

    condition = models.CharField(
        max_length=20,
        choices=CONDITION_CHOICES,
        default='good'
    )

    notes = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return self.name
    
    
class Warranty(models.Model):

    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expiring', 'Expiring Soon'),
        ('expired', 'Expired'),
    ]

    asset = models.OneToOneField(
        Asset,
        on_delete=models.CASCADE,
        related_name='warranty'
    )

    provider = models.CharField(
        max_length=150,
        blank=True
    )

    warranty_number = models.CharField(
        max_length=100,
        blank=True
    )

    start_date = models.DateField()

    end_date = models.DateField()

    coverage = models.TextField(
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.asset.name} Warranty"
    
    
class Maintenance(models.Model):

    MAINTENANCE_TYPES = [
        ('service', 'Service'),
        ('repair', 'Repair'),
        ('cleaning', 'Cleaning'),
        ('inspection', 'Inspection'),
        ('replacement', 'Replacement'),
        ('other', 'Other'),
    ]

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='maintenance_records'
    )

    maintenance_type = models.CharField(
        max_length=30,
        choices=MAINTENANCE_TYPES,
        default='service'
    )

    service_date = models.DateField()

    cost = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    service_provider = models.CharField(
        max_length=150,
        blank=True
    )

    description = models.TextField(
        blank=True
    )

    next_service_date = models.DateField(
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    updated_at = models.DateTimeField(
        auto_now=True
    )

    def __str__(self):
        return f"{self.asset.name} - {self.maintenance_type}"
    
    
class Document(models.Model):

    DOCUMENT_TYPES = [
        ('invoice', 'Invoice'),
        ('warranty', 'Warranty Card'),
        ('receipt', 'Service Receipt'),
        ('manual', 'User Manual'),
        ('insurance', 'Insurance'),
        ('property', 'Property Document'),
        ('other', 'Other'),
    ]

    home = models.ForeignKey(
        Home,
        on_delete=models.CASCADE,
        related_name='documents'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.CASCADE,
        related_name='documents',
        null=True,
        blank=True
    )

    name = models.CharField(
        max_length=150
    )

    document_type = models.CharField(
        max_length=30,
        choices=DOCUMENT_TYPES,
        default='other'
    )

    file = models.FileField(
        upload_to='documents/'
    )

    description = models.TextField(
        blank=True
    )

    uploaded_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.name
    
    
class Expense(models.Model):

    EXPENSE_TYPES = [
        ('purchase', 'Purchase'),
        ('maintenance', 'Maintenance'),
        ('repair', 'Repair'),
        ('service', 'Service'),
        ('other', 'Other'),
    ]

    home = models.ForeignKey(
        Home,
        on_delete=models.CASCADE,
        related_name='expenses'
    )

    asset = models.ForeignKey(
        Asset,
        on_delete=models.SET_NULL,
        related_name='expenses',
        null=True,
        blank=True
    )

    maintenance = models.ForeignKey(
        Maintenance,
        on_delete=models.SET_NULL,
        related_name='expense_records',
        null=True,
        blank=True
    )

    title = models.CharField(
        max_length=150
    )

    expense_type = models.CharField(
        max_length=30,
        choices=EXPENSE_TYPES,
        default='other'
    )

    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2
    )

    expense_date = models.DateField()

    description = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return self.title
    
    
class Notification(models.Model):
    TYPE_CHOICES = [
        ('warranty', 'Warranty Reminder'),
        ('maintenance', 'Maintenance Reminder'),
        ('expense', 'Expense Alert'),
        ('home', 'Home Alert'),
    ]

    home = models.ForeignKey(
        Home,
        on_delete=models.CASCADE,
        related_name='notifications'
    )

    title = models.CharField(max_length=200)

    message = models.TextField()

    notification_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES
    )

    is_read = models.BooleanField(default=False)

    reference_key = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title