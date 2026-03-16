
from django.db import models

class Service(models.Model):
    name=models.CharField(max_length=200)
    price=models.DecimalField(max_digits=8,decimal_places=2)

class Appointment(models.Model):
    customer_name=models.CharField(max_length=200)
    service=models.ForeignKey(Service,on_delete=models.CASCADE)
    date=models.DateField()
    time=models.TimeField()
