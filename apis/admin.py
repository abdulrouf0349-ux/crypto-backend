from django.contrib import admin
from .models import JobBank, AuthToken, InternationalJob, ScholorshipJob,Anoncment
# Register your models here.
@admin.register(JobBank)
class JobBankAdmin(admin.ModelAdmin):
    list_display = ('job_title', 'positions', 'Link', 'Job_apply_link', 'Image', )

@admin.register(AuthToken)
class AuthTokenAdmin(admin.ModelAdmin):
    list_display = ('user', 'token')

@admin.register(InternationalJob)
class InternationalJobAdmin(admin.ModelAdmin):
    list_display = ('title', 'link', 'image', 'short_description', 'scraped_at')
    search_fields = ('title', 'link')
    list_filter = ('scraped_at',)
    ordering = ('-scraped_at',)

@admin.register(ScholorshipJob)
class ScholorshipJobAdmin(admin.ModelAdmin):
    list_display= ('title', 'link' )
@admin.register(Anoncment)
class AnoncmentJobAdmin(admin.ModelAdmin):
    list_display= ('title', 'link' )