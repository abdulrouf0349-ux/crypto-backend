from django.http import JsonResponse
from .utils import token_required
from .models import JobBank, InternationalJob,InternationalJob,ScholorshipJob,jobz_pk,Anoncment
import json
from django.db.models import Q

@token_required
def my_secure_api(request):
    data = list(JobBank.objects.order_by("-date_time").values())  # positions will still be a JSON string
    for job in data:
        job['positions'] = json.loads(job['positions'])
        # ✅ decode JSON
    
    return JsonResponse(data, safe=False)


from django.http import JsonResponse, Http404
from .models import JobBank
from .utils import token_required  # Your custom auth decorator
import json

@token_required
def job_detail_by_slug(request, slug):
    try:
        job = JobBank.objects.get(slug=slug)
        job_data = {
            "job_title": job.job_title,
            "slug": job.slug,
            "Time": job.Time,
            "Link": job.Link,
            "Job_apply_link": job.Job_apply_link,
            "Image": job.Image,
            "positions": json.loads(job.positions),  # convert string back to list
            "date_time": job.date_time.isoformat(),
        }
        return JsonResponse(job_data, safe=False)
    except JobBank.DoesNotExist:
        raise Http404("Job not found")



from django.http import JsonResponse
from django.views.decorators.http import require_GET
from apis.models import JobBank
import json

@token_required
@require_GET
def filtered_jobs_view(request):
    location = request.GET.get('location')
    category = request.GET.get('category')
    keyword = request.GET.get('keyword')

    jobs = JobBank.objects.all().order_by("-date_time")

    if location:
        jobs = jobs.filter(location__icontains=location)
    if category:
        jobs = jobs.filter(positions__icontains=category)
    if keyword:
       jobs = jobs.filter(
        Q(job_title__icontains=keyword) |
        Q(positions__icontains=keyword)
    )
    data = []
    for job in jobs:
        data.append({
            "id": job.id,
            "job_title": job.job_title,
            "slug": job.slug,
            "Time": job.Time,
            "Image": job.Image,
            "Link": job.Link,
            "Job_apply_link": job.Job_apply_link,
            "positions": job.get_positions(),  # Convert JSON string to list
            "date_time": job.date_time,
            "location":job.location,  # if you have a `location` field
        })

    return JsonResponse(data, safe=False)



from django.http import JsonResponse
from django.db.models import Count, Q
from apis.models import JobBank
@token_required
@require_GET

def location_count_view(request):
    data = {
        "Punjab": JobBank.objects.filter(location__icontains="punjab").count(),
        "Sindh": JobBank.objects.filter(location__icontains="sindh").count(),
        "KPK": JobBank.objects.filter(location__icontains="kpk").count(),
        "Balochistan": JobBank.objects.filter(location__icontains="balochistan").count(),
        "Islamabad": JobBank.objects.filter(location__icontains="islamabad").count(),
        "Karachi": JobBank.objects.filter(location__icontains="karachi").count(),
        "Multan": JobBank.objects.filter(location__icontains="multan").count(),
        "Lahore": JobBank.objects.filter(location__icontains="lahore").count(),
        "Rawalpindi": JobBank.objects.filter(location__icontains="rawalpindi").count(),
    }
    return JsonResponse(data)
   
@token_required
@require_GET
def Region_data(request):
    region = request.GET.get('region')
    if region=='Govt':
      data = list(JobBank.objects.filter(location__icontains=region).order_by("-date_time").values())
      for job in data:
         job['positions'] = json.loads(job['positions']) 
    else:
        data = list(JobBank.objects.filter(location__icontains=region).order_by("date_time").values())
        for job in data:
         job['positions'] = json.loads(job['positions'])  # ✅ decode JSON
    if not region:
        return JsonResponse({"error": "Region parameter is required."}, status=400)
    

    return JsonResponse(data, safe=False)

@require_GET
@token_required
def myinternational_job(request):
    data = list(InternationalJob.objects.order_by("date_time").values())  # positions will still be a JSON string
    data.reverse()
    return JsonResponse(data, safe=False)


# @require_GET
# @token_required
# def Anoncement_d(request):
#     data = list(Anoncment.objects.values())  # positions will still be a JSON string
#     return JsonResponse(data, safe=False)
    

@require_GET
@token_required
def Anoncement_d(request):
    domain = 'https://nativeapi.site'
    data = []

    for obj in Anoncment.objects.all().order_by("-date_time"):
        data.append({
            'id': obj.id,
            'title': obj.title,  # example field
            'slug': obj.slug,  
            'image_main': domain + obj.image_main.url if obj.image_main else None,
            'heading5': obj.heading5,
            'deadline': obj.deadline,
            'expire_date': obj.expire_date,
            'date_time':obj.date_time,
            
        })
 

    return JsonResponse(data, safe=False)
from django.http import JsonResponse, Http404

@token_required
def Anoncement_d_slug(request, slug):
    try:
        job = Anoncment.objects.get(slug=slug)

        job_data = {
            'title': job.title,
            'title2': job.title2,
            'slug': job.slug,
            'link': job.link,
            'deadline': job.deadline,
            'expire_date': job.expire_date,
            'heading1': job.heading1,
            'discription1': job.discription1,
            'heading2': job.heading2,
            'discription2': job.discription2,
            'heading3': job.heading3,
            'discription3': job.discription3,
            'heading4': job.heading4,
            'discription4': job.discription4,
            'heading5': job.heading5,
            'discription5': job.discription5,
            'date_time':job.date_time,
            'image_main': request.build_absolute_uri(job.image_main.url) if job.image_main else None,
            'image2': request.build_absolute_uri(job.image2.url) if job.image2 else None,
            'disc_image': request.build_absolute_uri(job.disc_image.url) if job.disc_image else None,
            'disc_image2': request.build_absolute_uri(job.disc_image2.url) if job.disc_image2 else None,
        }

        return JsonResponse(job_data, safe=False)
    
    except Anoncment.DoesNotExist:
        raise Http404("Job not found")



@token_required
def inter_job_by_slug(request, slug):
    try:
        job = jobz_pk.objects.get(slug=slug)
        job_data={
                'title': job.title,
                'slug': job.slug,
                'web_link': job.web_link,
                'image': job.image,
                'company_title': job.company_title,
                'company_link': job.company_link,
                'city_title': job.city_title,
                'city_link': job.city_link,
                'date_job': job.date_job,
            }
        return JsonResponse(job_data, safe=False)
    except JobBank.DoesNotExist:
        raise Http404("Job not found")
    

@require_GET
@token_required
def scholorship_job(request):
    data = list(ScholorshipJob.objects.order_by("-date_time").values())  # positions will still be a JSON string
    data.reverse()
    return JsonResponse(data, safe=False)



@token_required
def scholorship_slug(request, slug):
    try:
        job = ScholorshipJob.objects.get(slug=slug)
        job_data = {
            "job_title": job.title,
            "slug": job.slug,
            "link": job.link,
            "requirment": job.requirment,
            "deadline": job.deadline,
            "expire_date_not": job.expire_date_not,  # convert string back to list
            "discription": job.discription,
        }
        return JsonResponse(job_data, safe=False)
    except JobBank.DoesNotExist:
        raise Http404("Job not found")




@token_required
def job_list_api(request):
    if request.method == 'GET':
        jobs = jobz_pk.objects.all().order_by("-date_time")
        data = []
        for job in jobs:
            data.append({
                'title': job.title,
                'slug': job.slug,
                'web_link': job.web_link,
                'image': job.image,
                'company_title': job.company_title,
                'company_link': job.company_link,
                'city_title': job.city_title,
                'city_link': job.city_link,
                'date_job': job.date_job,
            })
        data.reverse()

        return JsonResponse(data, safe=False)
    else:
        return JsonResponse({'error': 'Only GET allowed'}, status=405)