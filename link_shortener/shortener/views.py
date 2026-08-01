from django.shortcuts import render, get_object_or_404, redirect
from .models import ShortenedURL
from .forms import ShortenerForm

def home_view(request):
    """
    Handles the creation of new short URLs and manages the 
    user's recent history via session data.
    """
    # your code...

def redirect_url_view(request, short_code):
    """
    Finds the original URL for a given short code and 
    increments the analytics click counter.
    """
    # your code...

def redirect_url_view(request, short_code):
    """Increments click count for a URL and redirects the user to the original destination."""
    obj = get_object_or_404(ShortenedURL, short_code=short_code)

    obj.clicks += 1
    obj.save()

    return redirect(obj.original_url)


def home_view(request):
    """Handles the home page, URL submission form, and displays recently created links."""
    form = ShortenerForm(request.POST or None)
    new_url = None

    # Retrieve recent link IDs from the session
    recent_ids = request.session.get('recent_links',[])
    
    if request.method == "POST" and form.is_valid():
        obj = form.save()

        # Update session with the new ID and keep only the last 5
        recent_ids.append(obj.id)
        request.session['recent_links'] = recent_ids[-5:]
    
        new_url = request.build_absolute_uri('/') + obj.short_code

    # Fetch recent links from database based on session IDs
    recent_links = ShortenedURL.objects.filter(id__in=recent_ids).order_by('-created_at')
            
    context = {
            'form': form,
            'new_url': new_url,
            'recent_links': recent_links 
    }
    return render(request, 'shortener/home.html', context)