from django.shortcuts import redirect
from .forms import ReviewForm

def submit_review(request):
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            form.save()
    return redirect('/?avis=merci')
