from django.shortcuts import render, get_object_or_404, redirect
from .models import ShortenedURL
from .forms import ShortenerForm

def redirect_url_view(request, short_code):

    obj = get_object_or_404(ShortenedURL, short_code=short_code)
    return redirect(obj.original_url)


def home_view(request):
    form = ShortenerForm(request.POST or None)
    new_url = None
    
    if request.method == "POST":
        if form.is_valid():
            
            obj = form.save()
        
            new_url = request.build_absolute_uri('/') + obj.short_code
            
    context = {
        'form': form,
        'new_url': new_url
    }
    return render(request, 'shortener/home.html', context)