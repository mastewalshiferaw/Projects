from django.db import models
import string
import random

class ShortenedURL(models.Model):
    original_url = models.URLField()
    short_code = models.CharField(max_length=10, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    clicks = models.IntegerField(default=0)

    def save(self, *args, **kwargs):
        #short code hasn't been set yet, then
        if not self.short_code:
            self.short_code = self.generate_unique_code()
        super().save(*args, **kwargs)
    
    def generate_unique_code(self):
        chars = string.ascii_letters + string.digits
        while True:
            new_code = ''.join(random.choice(chars) for _ in range(6))

            #if it exits

            if not ShortenedURL.objects.filter(short_code=new_code).exists():
                return new_code