from django.shortcuts import render
from reviews.models import Review
from reviews.forms import ReviewForm

def home(request):
    reviews = Review.objects.filter(approved=True)[:6]
    form = ReviewForm()
    submitted = request.GET.get('avis') == 'merci'
    return render(request, "core/home.html", {
        'reviews': reviews,
        'form': form,
        'submitted': submitted,
    })
