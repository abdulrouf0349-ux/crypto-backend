

from django.http import JsonResponse
from apiapp.management.commands.timecalculate import get_time_difference
from django.core.paginator import Paginator
import json
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q
from .models import CoinpediaEvent,IcoProject,WhaleAlert,AllNews,Article
from datetime import datetime
VALID_LOCALES = ['en', 'de', 'es', 'fr', 'ru', 'ur', 'zh-cn','ar']
BASE_URL = 'http://127.0.0.1:8000'









# get all news data 
@csrf_exempt
def scrape_news_view(request, locale='en'):
    if request.method != 'POST':
        return JsonResponse({"error": "Method not allowed"}, status=405)
    valid_locales = ['de', 'es','ar', 'fr', 'ru', 'ur', 'zh-cn']
    
    # Agar locale '2' ya koi aur invalid cheez aaye to 'en' kar do
    if locale not in valid_locales:
        locale = 'en'

    try:
        data = json.loads(request.body)
        news_type = data.get('news', 'all').lower()
    except:
        news_type = 'all'

    # --- Filtering Logic ---
    if news_type == 'all':
        if locale == 'en':
            news_list = AllNews.objects.all().order_by('-time')
        else:
            news_list = AllNews.objects.exclude(**{f"title_{locale}": ""}).order_by('-time')
    else:
        if locale == 'en':
            news_list = AllNews.objects.filter(
                Q(title__icontains=news_type) | Q(discription_main__icontains=news_type)
            ).order_by('-time')
        else:
            news_list = AllNews.objects.filter(
                **{f"title_{locale}__icontains": news_type}
            ).exclude(**{f"title_{locale}": ""}).order_by('-time')

    # --- Pagination ---
    try:
        # request.GET se page lo, agar kuch na mile ya kachra mile to '1' rakho
        page_param = request.GET.get('page', '1')
        
        # Check agar numeric hai, warna default to 1
        page_number = int(page_param) if str(page_param).isdigit() else 1
    except (ValueError, TypeError):
        page_number = 1

    paginator = Paginator(news_list, 10)
    
    try:
        page = paginator.page(page_number)
        api_data = []
        for news in page.object_list:
            # Time logic
            try:
                saved_time = news.time
                if isinstance(saved_time, str):
                    saved_time = datetime.strptime(saved_time.split('.')[0], '%Y-%m-%d %H:%M:%S')
                time_diff = get_time_difference(saved_time)
            except:
                time_diff = "Recently"

            api_data.append({
                'id': news.id,
                'title': getattr(news, f"title_{locale}", news.title) if locale != 'en' else news.title,
                'slug': news.slug,
                'image': f"{BASE_URL}{news.image.url}" if news.image else None,
                'description': getattr(news, f"discription_main_{locale}", news.discription_main) if locale != 'en' else news.discription_main,
                'time': time_diff,
                'domain': news.domain,
            })

        return JsonResponse({
            "results": api_data,
            "total_pages": paginator.num_pages,
            "current_page": page.number
        })
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=404)








# get news slug 
@csrf_exempt
def get_news_by_id(request, locale='en'):

    if request.method != 'POST':
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    try:
        body = json.loads(request.body)
        slug = body.get("slug")

        if not slug:
            return JsonResponse({"error": "Slug is required"}, status=400)

        # Fetch single news
        try:
            news = AllNews.objects.get(slug=slug)
        except AllNews.DoesNotExist:
            return JsonResponse({"error": "News not found"}, status=404)

        # Time formatting
        saved_time = datetime.strptime(str(news.time), '%Y-%m-%d %H:%M:%S.%f')
        time_diff = get_time_difference(saved_time)

        # -------------------------------
        #    Locale Based Data Return
        # -------------------------------
        if locale == 'en':
            title = news.title
            description = news.discription_main
        else:
            translated_title = getattr(news, f"title_{locale}", None)
            translated_description = getattr(news, f"discription_main_{locale}", None)

            # Fallback to English
            title = translated_title if translated_title else news.title
            description = translated_description if translated_description else news.discription_main

        api_data = {
            "id": news.id,
            "title": title,
            "title_en": news.title,
            "slug": news.slug,
            "image": f"{BASE_URL}{news.image.url}" if news.image else None,
            "description": description,
            "Discription": "",
            "time": time_diff,
            "link": news.link,
            "domain": news.domain,
            "created_time": news.created_time,
        }

        return JsonResponse(api_data, safe=False)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)





@csrf_exempt
def get_news_type(request, locale="en"):
    try:
        body_data = json.loads(request.body)
        news_type = body_data.get("news", "").lower()

        if not news_type:
            return JsonResponse({'error': 'News type is required.'}, status=400)

        # --------------------------
        # 1. Filter by locale
        # --------------------------
        if locale == "en":
            # Default English
            news_items = AllNews.objects.filter(
                title__icontains=news_type
            ).order_by("-time")

        else:
            # For localized results (fr, ur, zh, etc.)
            localized_field = f"title_{locale}"
            news_items = AllNews.objects.exclude(
                **{f"{localized_field}__isnull": True}
            ).exclude(
                **{f"{localized_field}": ""}
            ).filter(
                **{f"{localized_field}__icontains": news_type}
            ).order_by("-time")

        # --------------------------
        # 2. Pagination
        # --------------------------
        page_number = int(request.GET.get("page", 1))
        paginator = Paginator(news_items, 10)

        try:
            page = paginator.page(page_number)
        except Exception:
            return JsonResponse({"error": "Page not found"}, status=404)

        # --------------------------
        # 3. Build API Data
        # --------------------------
        api_data = []
        for news in page.object_list:

            saved_time = datetime.strptime(str(news.time), "%Y-%m-%d %H:%M:%S.%f")
            time_diff = get_time_difference(saved_time)

            if locale == "en":
                # English Default Fields
                title = news.title
                description = news.discription_main
            else:
                # Get translated fields dynamically
                title = getattr(news, f"title_{locale}")
                description = getattr(news, f"discription_main_{locale}")

            api_data.append({
                "id": news.id,
                "title": title,
                "title_en": news.title,
                "slug": news.slug,
                "image": f"{BASE_URL}{news.image.url}" if news.image else None,
                "description": description,
                "time": time_diff,
                "link": news.link,
                "domain": news.domain,
                "created_time": news.created_time
            })

        # --------------------------
        # 4. Final Response
        # --------------------------
        return JsonResponse({
            "results": api_data,
            "total_pages": paginator.num_pages,
            "current_page": page.number,
            "next_page": page.next_page_number() if page.has_next() else None,
            "previous_page": page.previous_page_number() if page.has_previous() else None
        })

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON format'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)






















def get_all_ico_data(request, locale='en'):
    # --- Valid Locales Check ---
    valid_locales = ['de', 'es','ar', 'fr', 'ru', 'ur', 'zh-cn']
    if not locale or locale not in valid_locales:
        locale = 'en'

    # --- Params from URL ---
    status_filter = request.GET.get('status') # e.g., 'upcoming', 'ended', 'active'
    page_number = request.GET.get('page', 1)  # Default page 1

    try:
        # Base Query
        if locale == 'en':
            projects = IcoProject.objects.all().order_by('-created_at')
        else:
            projects = IcoProject.objects.exclude(**{f"name_{locale}": ""}).order_by('-created_at')

        # --- Status Filter Logic ---
        if status_filter:
            projects = projects.filter(status__iexact=status_filter)
        # --- Pagination Logic (10 data per page) ---
        paginator = Paginator(projects, 10) 
        page_obj = paginator.get_page(page_number)

        data_list = []
        for p in page_obj:
            # Dynamic Attribute Logic
            p_name = getattr(p, f"name_{locale}", p.name) if locale != 'en' else p.name
            p_type = getattr(p, f"project_type_{locale}", p.project_type) if locale != 'en' else p.project_type
            p_desc = getattr(p, f"description_{locale}", p.description) if locale != 'en' else p.description

            data_list.append({
                "id": p.id,
                "name": p_name or p.name,
                "project_type": p_type or p.project_type,
                "description": p_desc or p.description,
                "detail_link": p.detail_link,
                "main_img": p.main_image_url if hasattr(p, 'main_image_url') else p.main_img,
                "footer_img": p.footer_img,
                "raised_text": p.raised_text,
                "status_time": p.status_time,
                "investors_summary": p.investors_summary,
                "status": p.status,
                "slug": p.slug,
                "category_name": p.category_name,
                "website": p.website,
                "whitepaper": p.whitepaper,
                "twitter": p.twitter,
                "rounds_data": p.rounds_data,
                "overview_data": p.overview_data,
                "screenshots": p.screenshots,
                "created_at": p.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return JsonResponse({
            "status": "success",
            "locale": locale,
            "current_page": page_obj.number,
            "total_pages": paginator.num_pages,
            "has_next": page_obj.has_next(),
            "count": len(data_list),
            "data": data_list
        }, safe=False, status=200)

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)











def _serialize(p, locale):
    """Shared serializer — all model fields, locale-aware."""
    is_en = locale == 'en'

    def loc(field):
        """Return locale field if not empty, else English fallback."""
        if is_en:
            return getattr(p, field, None)
        return getattr(p, f"{field}_{locale}", None) or getattr(p, field, None)

    return {
        "id":               p.id,
        # ── locale-aware ────────────────────────────────
        "name":             loc("name"),
        "project_type":     loc("project_type"),
        "description":      loc("description"),
        # ── always English ───────────────────────────────
        "slug":             p.slug,
        "ticker":           p.ticker,
        "status":           p.status,
        "status_time":      p.status_time,
        "last_updated":     p.last_updated,
        "detail_link":      p.detail_link,
        "main_img":         p.main_img,
        "footer_img":       p.footer_img,
        "category_name":    p.category_name,
        # ── financials ───────────────────────────────────
        "raised_text":      p.raised_text,
        "pre_valuation":    p.pre_valuation,
        "rounds_count":     p.rounds_count,
        "investors_summary":p.investors_summary,
        # ── social links ─────────────────────────────────
        "website":          p.website,
        "whitepaper":       p.whitepaper,
        "twitter":          p.twitter,
        "discord":          p.discord,
        "telegram":         p.telegram,
        # ── JSON fields ──────────────────────────────────
        "rounds_data":      p.rounds_data,    # list of round dicts
        "overview_data":    p.overview_data,  # {total_raised, pre_valuation, rounds_count, last_updated}
        "screenshots":      p.screenshots,    # list of {src, name, type}
        # ── meta ─────────────────────────────────────────
        "created_at":       p.created_at.strftime("%Y-%m-%d %H:%M:%S"),
    }


def get_all_ico_data(request, locale='en'):
    if locale not in VALID_LOCALES:
        locale = 'en'

    status_filter = request.GET.get('status')
    page_number   = request.GET.get('page', 1)

    try:
        projects = IcoProject.objects.all().order_by('-created_at')

        if status_filter:
            projects = projects.filter(status__iexact=status_filter)

        paginator = Paginator(projects, 10)
        page_obj  = paginator.get_page(page_number)

        data_list = [_serialize(p, locale) for p in page_obj]

        return JsonResponse({
            "success":      True,
            "locale":       locale,
            "current_page": page_obj.number,
            "total_pages":  paginator.num_pages,
            "has_next":     page_obj.has_next(),
            "count":        len(data_list),
            "data":         data_list,
        }, status=200)

    except Exception as e:
        return JsonResponse({"success": False, "message": str(e)}, status=500)



@csrf_exempt
def get_ico_by_slug(request, locale='en'):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST allowed"}, status=405)

    if locale not in VALID_LOCALES:
        locale = 'en'

    try:
        body = json.loads(request.body)
        slug = body.get("slug", "").strip()

        if not slug:
            return JsonResponse({"error": "Slug is required"}, status=400)

        ico_obj = IcoProject.objects.filter(slug=slug).first()
        if not ico_obj:
            return JsonResponse({"error": "Project not found"}, status=404)

        return JsonResponse({
            "success": True,
            "locale":  locale,
            "data":    _serialize(ico_obj, locale),
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON body"}, status=400)
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)



@csrf_exempt
def get_all_alerts_callable(request, locale=None):
    """
    Returns a complete JSON response of whale alerts with
    ALL model fields, Pagination (10 per page) and Locale handling.
    """
    try:
        # 1. Locale Handle
        if locale == 'undefined' or not locale:
            locale = request.GET.get('locale', 'en').lower()
        else:
            locale = locale.lower()

        valid_langs = ['en', 'ur','ar', 'ru', 'es', 'fr', 'de', 'zh-cn']
        if locale not in valid_langs:
            locale = 'en'

        # 2. Pagination
        raw_page = request.GET.get('page', '1')
        page_number = int(raw_page) if str(raw_page).isdigit() else 1

        # 3. Queryset
        alerts_query = WhaleAlert.objects.all().order_by('-created_at')

        # 4. Paginator (10 per page)
        paginator = Paginator(alerts_query, 10)
        try:
            page_obj = paginator.page(page_number)
        except Exception:
            page_obj = paginator.page(1)

        # 5. Serialize — ALL model fields
        is_en = (locale == 'en')
        results = []

        for alert in page_obj:

            # ── Summary (translated if available) ─────────────────────
            summary_field = f"summary_{locale}" if not is_en else "summary"
            summary_value = getattr(alert, summary_field, None) or alert.summary

            results.append({

                # ── Core ──────────────────────────────────────────────
                "id":               alert.id,
                "summary":          summary_value,
                "url":              alert.url,
                "blockchain":       alert.blockchain,
                "timestamp_text":   alert.timestamp_text,
                "hash":             alert.transaction_hash,
                "transaction_hash": alert.transaction_hash,  # alias for UI compatibility

                # ── Fee / Price ───────────────────────────────────────
                "fee":              alert.fee,
                "fee_usd":          alert.fee_usd,
                "asset_price":      alert.asset_price,

                # ── Alert Card Fields ─────────────────────────────────
                "icon_url":         alert.icon_url,
                "amount_full":      alert.amount_full,
                "alert_text":       alert.alert_text,
                "alert_timestamp":  alert.alert_timestamp,
                "alert_type":       alert.alert_type,
                "emoticons":        alert.emoticons,
                "social_links":     alert.social_links,
                "tx_card_title":    alert.tx_card_title,

                # ── Transaction Detail ────────────────────────────────
                "timestamp_utc":        alert.timestamp_utc,
                "transaction_hash_url": alert.transaction_hash_url,

                # ── Sender ────────────────────────────────────────────
                "sender": {
                    "owner":       alert.sender_owner,
                    "address":     alert.sender_address,
                    "address_url": alert.sender_address_url,
                    "amount":      alert.sender_amount_crypto,
                    "amount_usd":  alert.sender_amount_usd,
                },

                # ── Receiver ──────────────────────────────────────────
                "receiver": {
                    "owner":       alert.receiver_owner,
                    "address":     alert.receiver_address,
                    "address_url": alert.receiver_address_url,
                    "amount":      alert.receiver_amount_crypto,
                    "amount_usd":  alert.receiver_amount_usd,
                },

                # ── Summary Translations ──────────────────────────────
                "translations": {
                    lang: getattr(alert, f"summary_{lang}", None)
                    for lang in ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
                },

                # ── Meta ──────────────────────────────────────────────
                "date_added": alert.created_at.strftime("%Y-%m-%d %H:%M:%S") if alert.created_at else None,
            })

        # 6. Final Response
        return JsonResponse({
            "status": "success",
            "metadata": {
                "total_results":  paginator.count,
                "total_pages":    paginator.num_pages,
                "current_page":   page_obj.number,
                "locale_active":  locale,
            },
            "data": results
        }, safe=False, json_dumps_params={'indent': 2}, status=200)

    except Exception as e:
        print(f"Error in get_all_alerts_callable: {e}")
        return JsonResponse({
            "status": "error",
            "message": str(e),
            "data": []
        }, status=500)







def get_all_events(request, locale=None): # locale=None lazmi hai
    try:
        # 1. Locale Handle
        # Pehle URL se locale check karein, agar wahan undefined ya khali ho to Query Param check karein, warna 'en'
        if locale == 'undefined' or not locale:
            locale = request.GET.get('locale', 'en').lower()
        else:
            locale = locale.lower()

        # Valid languages check (taake kachra data se crash na ho)
        valid_langs = ['en', 'ur','ar', 'ru', 'es', 'fr', 'de', 'zh-cn']
        if locale not in valid_langs:
            locale = 'en'
        
        # 2. Pagination Fix
        raw_page = request.GET.get('page', '1')
        page_number = int(raw_page) if str(raw_page).isdigit() else 1
        
        # 3. Queryset
        events_query = CoinpediaEvent.objects.all().order_by('-created_at')

        # 4. Paginator
        paginator = Paginator(events_query, 10)
        try:
            page_obj = paginator.page(page_number)
        except:
            page_obj = paginator.page(1)

        # 5. Model Fields Mapping
        events_list = []
        for event in page_obj:
            is_en = locale == 'en'
            events_list.append({
                'id': event.id,
                'title': getattr(event, f"title_{locale}", event.title) if not is_en else event.title,
                'detail_title': getattr(event, f"detail_title_{locale}", event.detail_title) if not is_en else event.detail_title,
                'description': getattr(event, f"description_{locale}", event.description) if not is_en else event.description,
                'location': getattr(event, f"location_{locale}", event.location) if not is_en else event.location,
                'detail_location': getattr(event, f"detail_location_{locale}", event.detail_location) if not is_en else event.detail_location,
                'organized_by': getattr(event, f"organized_by_{locale}", event.organized_by) if not is_en else event.organized_by,
                'date_text': event.date_text,
                'full_url': event.full_url,
                'maps_link': event.maps_link,
                'website_link': event.website_link,
                'image_src': event.image_src,
                'status': event.status,
                'slug': event.slug,
                'created_at': event.created_at.strftime("%Y-%m-%d %H:%M:%S")
            })

        return JsonResponse({
            "status": "success",
            "metadata": {
                "total_events": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "locale_active": locale
            },
            "data": events_list
        }, safe=False, json_dumps_params={'indent': 2}, status=200)

    except Exception as e:
        return JsonResponse({"status": "error", "error_detail": str(e)}, status=500)   




@csrf_exempt
def get_event_by_slug(request,locale='en'):
    """
    Fetch a single Coinpedia Event using its slug.
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)
    valid_langs = ['en', 'ur','ar', 'ru', 'es', 'fr', 'de', 'zh-cn']
   
    try:
        body   = json.loads(request.body)
        slug   = body.get("slug")

        if locale not in valid_langs:
            locale = 'en'

        if not slug:
            return JsonResponse({"status": "error", "message": "Slug is required"}, status=400)

        # Pehle English slug se dhundo
        event_obj = CoinpediaEvent.objects.filter(slug=slug).first()

        # Na mile to locale slug se try karo
        if not event_obj and locale != 'en':
            event_obj = CoinpediaEvent.objects.filter(
                **{f"slug_{locale}": slug}
            ).first()

        if not event_obj:
            return JsonResponse({
                "status": "error",
                "message": f"No event found with slug: {slug}"
            }, status=404)

        is_en = locale == 'en'
        e     = event_obj

        event_data = {
            'id':              e.id,
            'title':           getattr(e, f"title_{locale}",           e.title)           if not is_en else e.title,
            'detail_title':    getattr(e, f"detail_title_{locale}",    e.detail_title)    if not is_en else e.detail_title,
            'description':     getattr(e, f"description_{locale}",     e.description)     if not is_en else e.description,
            'location':        getattr(e, f"location_{locale}",        e.location)        if not is_en else e.location,
            'detail_location': getattr(e, f"detail_location_{locale}", e.detail_location) if not is_en else e.detail_location,
            'organized_by':    getattr(e, f"organized_by_{locale}",    e.organized_by)    if not is_en else e.organized_by,
            # ✅ slug locale-aware
            'slug':            getattr(e, f"slug_{locale}",            e.slug)            if not is_en else e.slug,
            'date_text':       e.date_text,
            'full_url':        e.full_url,
            'maps_link':       e.maps_link,
            'website_link':    e.website_link,
            'image_src':       e.image_src,
            'status':          e.status,
        }

        return JsonResponse({
            "status": "success",
            "data": event_data
        }, json_dumps_params={'indent': 2}, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON in request body"}, status=400)
    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": "Something went wrong",
            "error_detail": str(e)
        }, status=500)









@csrf_exempt
def get_all_articles(request, locale='en'):
    try:
        # 1. Locale Validation (Direct & Clean)
        locale = locale.lower() if locale else 'en'
        if locale not in VALID_LOCALES:
            locale = 'en'
        
        is_en = (locale == 'en')

        # 2. Filters & Pagination Params
        category = request.GET.get('category')
        page_num = request.GET.get('page', '1')
        page_size = 10 # Aap isay dynamic bhi kar sakte hain

        # 3. Optimized Queryset
        # .only() ya .defer() use karne se performance barhti hai agar content bohat heavy ho
        articles_query = Article.objects.filter(is_published=True).order_by('-created_at')
        
        if category:
            articles_query = articles_query.filter(category=category)

        # 4. Pagination
        paginator = Paginator(articles_query, page_size)
        page_obj = paginator.get_page(page_num) # .get_page khud errors handle kar leta hai

        base_url = request.build_absolute_uri('/')[:-1]
        articles_list = []

        for article in page_obj:
            # Helper function for cleaner code
            def get_field(field_name):
                if is_en:
                    return getattr(article, field_name, "N/A")
                # Locale field check, fallback to English
                return getattr(article, f"{field_name}_{locale}", None) or getattr(article, field_name, "N/A")

            # Image logic
            image_url = f"{base_url}{article.main_image.url}" if article.main_image else None

            articles_list.append({
                "id": article.id,
                "title": get_field('title'),
                "slug": get_field('slug'),
                "author": article.author,
                "category": article.category,
                "category_display": article.get_category_display(),
                "main_image": image_url,
                "content": get_field('content'),
                "meta_description": get_field('meta_description'),
                
                # Client-side switching ke liye sirf zaroori translations dein
                "translations": {
                    lang: {
                        "title": getattr(article, f"title_{lang}", None),
                        "slug": getattr(article, f"slug_{lang}", None),
                    } for lang in LANGS
                },
                
                "created_at": article.created_at.strftime("%Y-%m-%d") if article.created_at else None,
            })

        # 5. Professional Response
        return JsonResponse({
            "status": "success",
            "metadata": {
                "total_results": paginator.count,
                "total_pages": paginator.num_pages,
                "current_page": page_obj.number,
                "has_next": page_obj.has_next(),
                "locale_active": locale,
            },
            "data": articles_list
        }, safe=False, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)



@csrf_exempt
def get_article_by_slug(request, slug):
    try:
        # Slug ke zariye single article filter karna
        article_data = Article.objects.filter(slug=slug, is_published=True).values(
            'id', 
            'title', 
            'slug', 
            'author', 
            'main_image', 
            'category', 
            'content', 
            'meta_description', 
            'created_at'
        ).first()

        if not article_data:
            return JsonResponse({
                "status": "error",
                "message": "Article not found"
            }, status=404)

        # Base URL for images
        base_url = request.build_absolute_uri('/')[:-1] 

        # Image path ko full URL mein convert karna
        if article_data['main_image']:
            article_data['main_image'] = f"{base_url}/media/{article_data['main_image']}"
        
        # Date format fix
        if article_data['created_at']:
            article_data['created_at'] = article_data['created_at'].strftime("%Y-%m-%d %H:%M:%S")

        return JsonResponse({
            "status": "success",
            "data": article_data
        }, safe=False, json_dumps_params={'indent': 2})

    except Exception as e:
        return JsonResponse({
            "status": "error",
            "message": str(e)
        }, status=500)



@csrf_exempt
def get_whales_slug(request):
    """
    POST request se transaction_hash aur locale leta hai aur 
    alert ki puri nested details translated summary ke sath return karta hai.
    """
    if request.method != 'POST':
        return JsonResponse({"status": "error", "message": "Only POST allowed"}, status=405)

    try:
        # Request body se data nikalna
        body = json.loads(request.body)
        tx_hash = body.get("transaction_hash")
        locale = body.get("locale", "en").lower() # Default to 'en'

        if not tx_hash:
            return JsonResponse({"status": "error", "message": "transaction_hash is required"}, status=400)

        # Locale validation
        valid_langs = ['en', 'ur','ar', 'ru', 'es', 'fr', 'de', 'zh-cn']
        if locale not in valid_langs:
            locale = 'en'

        # Single alert fetch karna
        alert = WhaleAlert.objects.filter(transaction_hash=tx_hash).first()

        if not alert:
            return JsonResponse({
                "status": "error", 
                "message": "No alert found with this hash"
            }, status=404)

        # Logic for translated summary
        is_en = locale == 'en'
        summary_field = f"summary_{locale}"
        translated_summary = getattr(alert, summary_field, alert.summary) if not is_en else alert.summary

        # Response structure
        data = {
            "id": alert.id,
            "summary": translated_summary, # Translated summary yahan set hogi
            "url": alert.url,
            "blockchain": alert.blockchain,
            "timestamp": alert.timestamp_text,
            "hash": alert.transaction_hash,
            "fee": alert.fee,
            "price": alert.asset_price,
            "sender": {
                "owner": alert.sender_owner,
                "address": alert.sender_address,
                "amount": alert.sender_amount_crypto
            },
            "receiver": {
                "owner": alert.receiver_owner,
                "address": alert.receiver_address,
                "amount": alert.receiver_amount_crypto
            },
            "date_added": alert.created_at.strftime("%Y-%m-%d %H:%M:%S") if alert.created_at else None,
            "locale_active": locale
        }

        return JsonResponse({
            "status": "success",
            "data": data
        }, status=200)

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        print(f"Error in get_whales_slug: {e}")
        return JsonResponse({
            "status": "error", 
            "message": str(e)
        }, status=500)