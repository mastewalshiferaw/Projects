from django.shortcuts import render, get_object_or_404, redirect
from .models import ShortenedURL
from .forms import ShortenerForm

def redirect_url_view(request, short_code):
    
    obj = get_object_or_404(ShortenedURL, short_code=short_code)

    obj.clicks += 1
    obj.save()

    return redirect(obj.original_url)


def home_view(request):
    form = ShortenerForm(request.POST or None)
    new_url = None

    recent_ids = request.session.get('recent_links', [])
    
    if request.method == "POST":
        if form.is_valid():
            obj = form.save()

            recent_ids.append(obj.id)
            request.session['recent_links'] = recent_ids[-5:]
        
            new_url = request.build_absolute_uri('/') + obj.short_code

    recent_links = ShortenedURL.objects.filter(id__in=recent_ids).order_by('-created_at')
            
    context = {
            'form': form,
            'new_url': new_url,
            'recent_links': recent_links 
    }
    return render(request, 'shortener/home.html', context)