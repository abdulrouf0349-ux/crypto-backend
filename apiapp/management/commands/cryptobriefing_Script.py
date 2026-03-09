from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from apiapp.models import AllNews
from datetime import datetime
import re
from django.db.models import Q
from django.utils.text import slugify
from apiapp.management.commands.parsedtime import parse_time_ago
from django.core.files import File
from io import BytesIO
from apiapp.translate_ai import translate_to_lang  # your Google Translate wrapper
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
    help = 'Scrapes news from CryptoBriefing and translates into multiple languages'

    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

    def handle(self, *args, **kwargs):
        response = requests.get('https://cryptobriefing.com')
        if response.status_code != 200:
            self.stdout.write(f"Error fetching the website, status code: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        section = soup.find('section', class_='main-news loadmore-container-wrapper')
        if not section:
            self.stdout.write("Error: No main news section found.")
            return

        section_div = section.find('ul', class_='main-news-list loadmore-container')
        if not section_div:
            self.stdout.write("Error: No news list container found.")
            return

        saved_count = 0
        duplicate_count = 0

        for d in section_div.find_all('li', class_='main-news-item')[:3]:  # Limit to first 3 for demo
            try:
                div_1 = d.find('div', class_='main-news-info')
                if not div_1:
                    continue

                # Image
                div_img = div_1.find('div', class_='main-news-img')
                img = None
                if div_img:
                    picture_tag = div_img.find('picture')
                    img_tag = picture_tag.find('img') if picture_tag else None
                    img = img_tag.get('data-lazy-src') if img_tag else None

                # Title & Link
                title_h2 = div_1.find('h2', class_='main-news-title')
                a_tag = title_h2.find('a') if title_h2 else None
                href = a_tag.get('href') if a_tag else None
                title = title_h2.text.strip().strip('"').strip("'") if title_h2 else "No title"

                # Short description & time
                description_short = div_1.find('p', class_='main-news-message')
                time_p = div_1.find('p', class_='main-news-meta')
                time_text = time_p.find('time').text.strip() if time_p else "No time"
                dt = datetime.strptime(time_text, "%b. %d, %Y")
                dt_with_time = dt.replace(hour=0, minute=0, second=0, microsecond=0)
                formatted_time = parse_time_ago(time_text)

                # Full article description
                article_description = ""
                if href:
                    article_response = requests.get(href)
                    if article_response.status_code == 200:
                        article_soup = BeautifulSoup(article_response.content, 'html.parser')
                        article_section = article_soup.find('section', class_='article-content')
                        if article_section:
                            paragraphs = article_section.find_all('p')
                            article_description = " ".join([p.text.strip() for p in paragraphs])

                # Check duplicates
                if AllNews.objects.filter(Q(link=href) | Q(title=title)).exists():
                    duplicate_count += 1
                    self.stdout.write(f"Duplicate found: {title}")
                    continue

                # Save English news
                news = AllNews(
                    title=title,
                    slug=slugify(title),
                    discription_main=article_description,
                    discription=description_short.text.strip() if description_short else "",
                    time=dt_with_time,
                    link=href,
                    domain='cryptobriefing.com'
                )
                if img:
                    download_and_save_image(news, img)
                news.save()
                saved_count += 1

                # Translate to other languages
                for lang in self.LANGS:
                    try:
                        title_translated = translate_to_lang(title, lang)
                        desc_translated = translate_to_lang(article_description, lang)
                        setattr(news, f"title_{lang}", title_translated)
                        setattr(news, f"discription_{lang}", desc_translated)
                        setattr(news, f"discription_main_{lang}", desc_translated)
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
