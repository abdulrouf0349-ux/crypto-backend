from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from apiapp.models import AllNews
from apiapp.management.commands.parsedtime import parse_time_ago
from django.db.models import Q
from django.core.files import File
from io import BytesIO
from django.utils.text import slugify
from apiapp.translate_ai import translate_to_lang  # Your translation function
import time

def download_and_save_image(news_instance, image_url):
    try:
        response = requests.get(image_url)
        if response.status_code == 200:
            img_name = image_url.split("/")[-1]
            img_data = BytesIO(response.content)
            news_instance.image.save(img_name, File(img_data), save=True)
            news_instance.save()
            print(f"Image saved: {img_name}")
        else:
            print(f"Failed to download image: {response.status_code}")
    except Exception as e:
        print(f"Error saving image: {e}")

class Command(BaseCommand):
    help = 'Scrapes news from CryptoNews.net and translates into multiple languages'

    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

    def handle(self, *args, **kwargs):
        response = requests.get('https://cryptonews.net/')
        if response.status_code != 200:
            self.stdout.write(f"Error fetching website: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        data = soup.find_all('div', class_='row news-item start-xs')

        saved_count = 0
        duplicate_count = 0

        for d in data[:10]:  # Limit to first 10 articles
            try:
                img = d.get('data-image')
                domain = d.get('data-domain')
                title_raw = d.get('data-title')
                title = title_raw.strip('"').strip("'") if title_raw else "No title"
                href = d.get('data-link')
                dataid = d.get('data-id')

                # Time
                datetime_span = d.find('span', class_='datetime flex middle-xs')
                time_text = datetime_span.text.strip() if datetime_span else "No time"
                formatted_time = parse_time_ago(time_text)

                # Full description
                description_full = ''
                if dataid:
                    article_response = requests.get(f'https://cryptonews.net{dataid}')
                    if article_response.status_code == 200:
                        article_soup = BeautifulSoup(article_response.content, 'html.parser')
                        content_div = article_soup.find('div', class_='content')
                        description_div = content_div.find('div', class_='cn-content') if content_div else None
                        if description_div:
                            description_full = description_div.text.strip()

                # Check duplicates
                if AllNews.objects.filter(Q(link=href) | Q(title=title)).exists():
                    duplicate_count += 1
                    self.stdout.write(f"Duplicate found: {title}")
                    continue

                # Save English news
                news = AllNews(
                    title=title,
                    slug=slugify(title),
                    discription=description_full[:500],  # Short description field
                    discription_main=description_full,
                    time=formatted_time,
                    link=href,
                    domain=domain
                )
                if img:
                    download_and_save_image(news, img)
                news.save()
                saved_count += 1

                # Translate into multiple languages
                for lang in self.LANGS:
                    try:
                        title_translated = translate_to_lang(title, lang)
                        description_translated = translate_to_lang(description_full, lang)
                        setattr(news, f"title_{lang}", title_translated)
                        setattr(news, f"discription_{lang}", description_translated)
                        setattr(news, f"discription_main_{lang}", description_translated)
                        setattr(news, f"slug_{lang}", slugify(title_translated))
                        time.sleep(0.1)
                    except Exception as e:
                        self.stdout.write(f"[ERROR] Translation failed for {lang} | ID {news.id}: {e}")

                news.save()
                self.stdout.write(f"Saved and translated: {title}")

            except Exception as e:
                self.stdout.write(f"Error processing article: {e}")
                continue

        self.stdout.write(f"Scraping completed. Saved: {saved_count}, Duplicates: {duplicate_count}")
