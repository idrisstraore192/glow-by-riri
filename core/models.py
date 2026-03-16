
from django.db import models

class SiteSettings(models.Model):
    brand_name=models.CharField(max_length=120,default="Glow by Riri")
    slogan=models.CharField(max_length=255,blank=True)
