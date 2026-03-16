from django.urls import path
from .views import submit_review

urlpatterns = [
    path('soumettre/', submit_review, name='submit_review'),
]
