from django import forms
from .models import Review

class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ['name', 'rating', 'comment']
        widgets = {
            'name': forms.TextInput(attrs={'placeholder': 'Votre prénom'}),
            'rating': forms.Select(),
            'comment': forms.Textarea(attrs={'placeholder': 'Partagez votre expérience...', 'rows': 4}),
        }
        labels = {
            'name': 'Prénom',
            'rating': 'Note',
            'comment': 'Commentaire',
        }
