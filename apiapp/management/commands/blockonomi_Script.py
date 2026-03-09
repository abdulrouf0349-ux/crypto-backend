from django.core.management.base import BaseCommand
import requests
from django.db.models import Q
from bs4 import BeautifulSoup
from apiapp.models import AllNews
from datetime import datetime
from django.core.files import File
from io import BytesIO
from django.utils.text import slugify
import time
from django.utils.timezone import now as django_now


# Translation
from apiapp.translate_ai import translate_to_lang  # your existing Google Translate wrapper

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
    help = 'Scrapes news from Blockonomi and translates into multiple languages'

    LANGS = ['ur', 'ru','ar', 'es', 'fr', 'de', 'zh-CN']

    def handle(self, *args, **kwargs):
        response = requests.get('https://blockonomi.com/')
        if response.status_code != 200:
            self.stdout.write("Error fetching website")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        section = soup.find('div', class_="loop loop-grid loop-grid-base grid grid-3 md:grid-2 xs:grid-1")
        articles = section.find_all('article', class_='l-post grid-post grid-base-post')

        saved_count = 0
        duplicate_count = 0

        for d in articles[:20]:  # limit to first 20 for demo
            try:
                # Extract link & image
                div_1 = d.find('div', class_='media')
                a_Tag = div_1.find('a') if div_1 else None
                href = a_Tag.get('href') if a_Tag else None
                img_tag = a_Tag.find('span') if a_Tag else None
                img_url = ""
                if img_tag:
                    img_data = img_tag.get('data-bgset', '')
                    img_url = img_data.split(',')[0].strip().split()[0]

                # Extract title & time
                div_2 = d.find('div', class_='content')
                title_tag = div_2.find('h2', class_='is-title post-title limit-lines l-lines-3') if div_2 else None
                title = title_tag.text.strip().strip('"').strip("'") if title_tag else None

                time_tag = div_2.find('span', class_='date-link').find('time') if div_2 else None
                time_text = time_tag.text.strip() if time_tag else None
                if time_text:
                    dt = datetime.strptime(time_text, "%B %d, %Y")
                    # Professional tip: Microsecond ko 0 ki bajaye 100 rakhein 
                    # taaki string format hamesha .f ko support kare
                    dt_with_time = dt.replace(hour=12, minute=0, second=0, microsecond=100000)
                else:
                    dt_with_time = django_now()

                # Scrape full article description
                article_description = ""
                if href:
                    resp_article = requests.get(href)
                    if resp_article.status_code == 200:
                        soup_article = BeautifulSoup(resp_article.content, 'html.parser')
                        section2 = soup_article.find('div', class_='post-content cf entry-content content-spacious')
                        if section2:
                            paragraphs = section2.find_all('p')
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
                    time=dt_with_time,
                    link=href,
                    domain='blockonomi.com'
                )
                news.save()
                saved_count += 1

                # Translate into other languages
                for lang in self.LANGS:
                    try:
                        title_translated = translate_to_lang(title, lang)
                        desc_translated = translate_to_lang(article_description, lang)

                        setattr(news, f"title_{lang}", title_translated)
                        setattr(news, f"discription_{lang}", desc_translated)
                        setattr(news, f"discription_main_{lang}", desc_translated)
                        setattr(news, f"slug_{lang}", slugify(title_translated))
                    except Exception as e:
                        self.stdout.write(f"[ERROR] Translation failed for {lang} | ID {news.id}: {e}")

                news.save()  # Save translations
                download_and_save_image(news, img_url)

                self.stdout.write(f"Saved and translated: {title}")

            except Exception as e:
                self.stdout.write(f"Error processing article: {e}")
                continue

        self.stdout.write(f"Scraping completed. Saved: {saved_count}, Duplicates: {duplicate_count}")
