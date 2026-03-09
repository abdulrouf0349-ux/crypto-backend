from django.db import models
import json
from django.utils.text import slugify

# Create your models here.
class JobBank(models.Model):
    job_title = models.CharField(max_length=1000)
    slug = models.SlugField(unique=True, blank=True, null=True)  # ✅ NEW FIELD
    Time = models.CharField(max_length=255)
    Link = models.URLField(max_length=5000,null=True, blank=True)
    Job_apply_link = models.URLField(max_length=5000,null=True, blank=True)
    Image = models.URLField(max_length=5000, null=True, blank=True)
    positions = models.TextField()  # Store positions as JSON or delimited string
    date_time=models.DateTimeField(auto_now_add=True)
    location = models.CharField(max_length=255, null=True, blank=True)


    def __str__(self):
        return f"{self.job_title} "
    

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.job_title)  # ✅ Auto-generate from title
        super().save(*args, **kwargs)
        
    def save_positions(self, positions):
        # Store positions as JSON
        self.positions = json.dumps(positions)
        self.save()

    def get_positions(self):
        # Return positions as a list from JSON string
        return json.loads(self.positions)

  



from django.db import models

class AuthToken(models.Model):
    user = models.CharField(max_length=100)
    token = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return f"{self.user} - {self.token}"



from django.db import models

class InternationalJob(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)  # ✅ NEW FIELD
    link = models.URLField(unique=True)
    image = models.URLField(blank=True, null=True)
    short_description = models.TextField(blank=True, null=True)
    full_description = models.TextField(blank=True, null=True)
    scraped_at = models.DateTimeField(auto_now_add=True)
    date_time=models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-scraped_at']
        verbose_name = 'International Job'
        verbose_name_plural = 'International Jobs'

    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  # ✅ Auto-generate from title
        super().save(*args, **kwargs)





class ScholorshipJob(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, blank=True, null=True)  # ✅ NEW FIELD
    link = models.URLField(unique=True)
    requirment = models.TextField(blank=True, null=True)
    deadline = models.TextField(blank=True, null=True)
    expire_date_not = models.TextField(blank=True, null=True)
    discription = models.TextField(blank=True, null=True)
    date_time=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  # ✅ Auto-generate from title
        super().save(*args, **kwargs)





class jobz_pk(models.Model):
    title = models.CharField(max_length=255)
    slug = models.SlugField( blank=True, null=True)  # ✅ NEW FIELD
    web_link = models.URLField()
    image = models.URLField()
    company_title = models.CharField(max_length=255)
    company_link = models.URLField()
    city_title = models.CharField(max_length=255)
    city_link = models.URLField()
    date_job = models.CharField(max_length=255)
    date_time=models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  # ✅ Auto-generate from title
        super().save(*args, **kwargs)
        
        
        


class Anoncment(models.Model):
    title = models.CharField(max_length=500)
    title2 = models.CharField(max_length=500,blank=True)
    slug = models.SlugField(unique=True, blank=True, null=True)  # ✅ NEW FIELD
    link = models.URLField(blank=True)
    deadline = models.CharField(max_length=500,blank=True,null=True)
    expire_date = models.CharField(max_length=500,blank=True,null=True)
    heading1 = models.TextField(blank=True, null=True)
    discription1 = models.TextField(blank=True, null=True)
    heading2 = models.TextField(blank=True, null=True)
    discription2 = models.TextField(blank=True, null=True)
    heading3 = models.TextField(blank=True, null=True)
    discription3 = models.TextField(blank=True, null=True)
    heading4 = models.TextField(blank=True, null=True)
    discription4 = models.TextField(blank=True, null=True)
    heading5 = models.TextField(blank=True, null=True)
    discription5 = models.TextField(blank=True, null=True)
    image_main = models.ImageField(upload_to='images/',blank=True)
    image2 = models.ImageField(upload_to='images/',blank=True)
    disc_image = models.ImageField(upload_to='images/',blank=True)
    disc_image2 = models.ImageField(upload_to='images/',blank=True)
    date_time=models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.title
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)  # ✅ Auto-generate from title
        super().save(*args, **kwargs)