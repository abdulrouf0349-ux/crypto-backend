from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from apiapp.models import AllNews
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
    help = 'Scrapes news from CoinPaprika and translates into multiple languages'

    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

    def handle(self, *args, **kwargs):
        response = requests.get('https://coinpaprika.com/news/?category=general')
        if response.status_code != 200:
            self.stdout.write("Error fetching website")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        section = soup.find('section')
        section_Div = section.find('div', class_='news-page-grid')
        article_divs = section_Div.find_all('article', class_='news-page-card paprika-card')

        saved_count = 0
        duplicate_count = 0

        for d in article_divs[:6]:  # limit to first 6 articles for demo
            try:
                div_1 = d.find('div', class_='news-page-card__wrapper')

                # Link
                a_tag = div_1.find('a') if div_1 else None
                href = a_tag.get('href') if a_tag else None

                # Image
                img_tag = a_tag.find('img', class_='news-page-card__preview-image') if a_tag else None
                img_url = img_tag.get('src') if img_tag else None

                # Time
                time1 = div_1.find('div', class_='news-page-card__header') if div_1 else None
                time_text = time1.text.strip().replace(' ', '') if time1 else "No time"
                match = re.search(r'\((\d+)(sec|min|hour|hours|day|days)ago\)', time_text)
                formatted_time = f"{match.group(1)} {match.group(2)} ago" if match else "No time"
                time_format = parse_time_ago(formatted_time)

                # Title
                title_tag = div_1.find('a', class_='news-page-card__content') if div_1 else None
                title_span = title_tag.find('span', class_="news-page-card__title") if title_tag else None
                title = title_span.text.strip().strip('"').strip("'") if title_span else "No title"

                # Description from detailed page
                description = ""
                if href:
                    article_response = requests.get(href)
                    if article_response.status_code == 200:
                        article_soup = BeautifulSoup(article_response.content, 'html.parser')
                        section_content = article_soup.find('div', class_='news-article__content')
                        if section_content:
                            inner_div = section_content.find('div')
                            content_inner = inner_div.find('div', class_='news-article__content-inner') if inner_div else None
                            paragraphs = content_inner.find_all('p') if content_inner else []
                            description = " ".join([p.text.strip() for p in paragraphs])

                # Check duplicates
                if AllNews.objects.filter(Q(link=href) | Q(title=title)).exists():
                    duplicate_count += 1
                    self.stdout.write(f"Duplicate found: {title}")
                    continue

                # Save English news
                news = AllNews(
                    title=title,
                    slug=slugify(title),
                    discription_main=description,
                    time=time_format,
                    link=href,
                    domain='coinpaprika.com'
                )
                if img_url:
                    download_and_save_image(news, img_url)
                news.save()
                saved_count += 1

                # Translate to other languages
                for lang in self.LANGS:
                    try:
                        title_translated = translate_to_lang(title, lang)
                        desc_translated = translate_to_lang(description, lang)

                        setattr(news, f"title_{lang}", title_translated)
                        setattr(news, f"discription_{lang}", desc_translated)
                        setattr(news, f"discription_main_{lang}", desc_translated)
                        setattr(news, f"slug_{lang}", slugify(title_translated))
                        time.sleep(0.1)  # small delay to avoid rate limit
                    except Exception as e:
                        self.stdout.write(f"[ERROR] Translation failed for {lang} | ID {news.id}: {e}")

                news.save()  # save translations
                self.stdout.write(f"Saved and translated: {title}")

            except Exception as e:
                self.stdout.write(f"Error processing article: {e}")
                continue

        self.stdout.write(f"Scraping completed. Saved: {saved_count}, Duplicates: {duplicate_count}")
