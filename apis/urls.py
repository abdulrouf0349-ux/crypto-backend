from django.urls import path, include
from .views import my_secure_api,Anoncement_d_slug, job_detail_by_slug,Region_data,job_list_api,Anoncement_d, filtered_jobs_view,scholorship_slug, location_count_view,myinternational_job,scholorship_job,inter_job_by_slug
urlpatterns = [
    path('jobs/', my_secure_api),  # Include the URLs from the apis app
    # path('job-detail/<slug:slug>/', job_detail_by_slug, name='job_detail_by_slug'),
    path('job-detail/<path:slug>/', job_detail_by_slug),
    path('jobs/filter/', filtered_jobs_view),
    path('location-count/', location_count_view),
    path('scholorship_get/', scholorship_job),
    path('inter-jobs/', job_list_api, name='my_international_job'),

    path('inter_job_by_slug/<path:slug>/', inter_job_by_slug, name='inter_job_by_slug'),
    
    path('scholorships_get/<path:slug>/', scholorship_slug, name='scholorships_slug'),
    path('Region_data/', Region_data, name='Region_data'),
    path('Anoncement_data/', Anoncement_d, name='Anoncement_d'),
    path('Anoncement_d_s/<path:slug>/', Anoncement_d_slug, name='Anoncement_d_slug'),

    
    


    
]