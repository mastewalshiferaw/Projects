from django.shortcuts import render, get_object_or_404, redirect
from .models import ShortenedURL

def redirect_url_view(request, short_code):

    obj = get_object_or_404(ShortenedURL, short_code=short_code)
    return redirect(obj.original_url)

