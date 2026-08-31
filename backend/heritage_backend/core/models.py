from django.db import models

class Province(models.Model):
    province_id = models.AutoField(primary_key=True)
    name        = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name
    class Meta: ordering = ['name']


    
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name        = models.CharField(max_length=100, unique=True)
    def __str__(self): return self.name
    class Meta: ordering = ['name']

    
class HeritageSite(models.Model):
    site_id     = models.AutoField(primary_key=True)
    name        = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    entry_fee   = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    is_active   = models.BooleanField(default=True)
    province    = models.ForeignKey(Province, on_delete=models.PROTECT)
    category    = models.ForeignKey(Category, on_delete=models.PROTECT)
    def __str__(self): return f'{self.name} ({self.province})'
    class Meta: unique_together = [['name','province']]


class Visitor(models.Model):
    visitor_id = models.AutoField(primary_key=True)
    full_name  = models.CharField(max_length=255)
    email      = models.EmailField(unique=True)
    def __str__(self): return f'{self.full_name} <{self.email}>'


class Booking(models.Model):
    booking_id       = models.AutoField(primary_key=True)
    heritage_site    = models.ForeignKey(HeritageSite, on_delete=models.PROTECT)
    visitor          = models.ForeignKey(Visitor, on_delete=models.PROTECT)
    booking_date     = models.DateField(auto_now_add=True)
    visit_date       = models.DateField()
    number_of_people = models.PositiveIntegerField()
    is_cancelled     = models.BooleanField(default=False)
    cancelled_at     = models.DateTimeField(null=True, blank=True)
    def __str__(self): return f'Booking #{self.booking_id} — {self.heritage_site} on {self.visit_date}'
    class Meta:
        indexes = [
            models.Index(fields=['visit_date'],    name='booking_visit_date_idx'),
            models.Index(fields=['heritage_site'], name='booking_site_idx'),
            models.Index(fields=['booking_date'],  name='booking_date_idx'),
        ]

