
from django.db import models

class Product(models.Model):
    name=models.CharField(max_length=200)
    price=models.DecimalField(max_digits=8,decimal_places=2)
    description=models.TextField(blank=True)
    image=models.ImageField(upload_to="products/",blank=True,null=True)
