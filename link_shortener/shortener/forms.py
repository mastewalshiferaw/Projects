from django import forms
from .models import ShortenedURL

class ShortenerForm(forms.ModelForm):
    class Meta:
        model = ShortenedURL
        fields = ['original_url']

    def clean_original_url(self):
        url = self.cleaned_data['original_url']
        if "127.0.0.1" in url or "localhost" in url:
            raise ValidationError("You cannot shorten links from this website!")
        return url