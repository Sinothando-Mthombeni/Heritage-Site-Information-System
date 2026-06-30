from django.db import models

class Province(models.Model):
    province_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "province"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name
    
class Category(models.Model):
    category_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)

    class Meta:
        db_table = "category"
        indexes = [
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return self.name
    
class HeritageSite(models.Model):
    site_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField()
    entry_fee = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    is_active = models.BooleanField(default=True)

    province = models.ForeignKey(
        Province,
        on_delete=models.PROTECT,
        db_column="province_id"
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        db_column="category_id"
    )

    class Meta:
        db_table = "heritage_site"
        indexes = [
            models.Index(fields=["name"]),
            models.Index(fields=["province"]),
        ]
        unique_together = ("name", "province")

    def __str__(self):
        return self.name

class Visitor(models.Model):
    visitor_id = models.AutoField(primary_key=True)
    full_name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)

    class Meta:
        db_table = "visitor"
        indexes = [
            models.Index(fields=["email"]),
        ]

    def __str__(self):
        return self.full_name

class Booking(models.Model):
    booking_id = models.AutoField(primary_key=True)
    booking_date = models.DateField(auto_now_add=True)
    visit_date = models.DateField()
    number_of_people = models.PositiveIntegerField()

    visitor = models.ForeignKey(
        Visitor,
        on_delete=models.CASCADE,
        db_column="visitor_id"
    )

    heritage_site = models.ForeignKey(
        HeritageSite,
        on_delete=models.CASCADE,
        db_column="site_id"
    )

    class Meta:
        db_table = "booking"
        indexes = [
            models.Index(fields=["visit_date"]),
            models.Index(fields=["heritage_site"]),
        ]
