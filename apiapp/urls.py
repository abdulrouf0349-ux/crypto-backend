from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static
urlpatterns = [
 

    # 9th api get article id
    path('getdata/<str:locale>/',views.scrape_news_view, name='getdata'),   


    path('getdata/',views.scrape_news_view, name='getdata'),

    path('getnews/<str:locale>/', views.get_news_by_id, name='get-news-by-id'),
    path('getnews/', views.get_news_by_id, name='get-news-by-id'),
   
    path('get_news_type/<str:locale>/', views.get_news_type, name='get_news_type'),
  
    # path('data/', views.home, name='home'),

path('get-events/<str:locale>/', views.get_all_events, name='get_all_events'),
path('ico_data/<str:locale>/', views.get_all_ico_data, name='ico_data_locale'),
path('get_slug_ico/<str:locale>/', views.get_ico_by_slug, name='ico_data'),
path('whales_alert/<str:locale>/', views.get_all_alerts_callable, name='whale_alerts_api'),
path('get_slug_event/<str:locale>/', views.get_event_by_slug, name='get_event_by_slug'),
path('get_whales_slug/', views.get_whales_slug, name='get_whales_slug'),
path('get_all_articles/<str:locale>/', views.get_all_articles, name='get_all_articles'),
path('get_article_by_slug/<slug:slug>', views.get_article_by_slug, name='get_article_by_slug'),

]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)