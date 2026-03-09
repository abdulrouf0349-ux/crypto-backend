from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from django.db.models import Q
from django.utils.text import slugify
from datetime import datetime
from io import BytesIO
from django.core.files import File

from apiapp.models import AllNews
from apiapp.management.commands.parsedtime import parse_time_ago
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
            print(f"Image successfully saved: {img_name}")
        else:
            print(f"Failed to download image: {response.status_code}")
    except Exception as e:
        print(f"Error downloading or saving image: {e}")

class Command(BaseCommand):
    help = 'Scrapes news from Finbold and translates into multiple languages'

    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

    def handle(self, *args, **kwargs):
        response = requests.get('https://finbold.com/category/cryptocurrency-news/')
        if response.status_code != 200:
            self.stdout.write(f"Error fetching website: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        section = soup.find('div', class_='lg:col-span-2 mb-10 lg:mb-0')
        section_Div = section.find_all('div', class_='py-5 first:pt-0 last:pb-0') if section else []

        saved_count = 0
        duplicate_count = 0

        for d in section_Div:
            try:
                div_2 = d.find('div', class_='flex gap-x-4')
                a_Tag = div_2.find('a') if div_2 else None
                href = a_Tag.get('href') if a_Tag else None
                title3 = a_Tag.get('title') if a_Tag else "No title"
                title = title3.strip('"').strip("'")

                img_tag = div_2.find('img') if div_2 else None
                img = img_tag.get('src') if img_tag else None

                time1 = div_2.find('span', class_='self-center text-xs text-neutral-400') if div_2 else None
                time_text = time1.text.strip() if time1 else "No time"
                formatted_time = parse_time_ago(time_text)

                # Scrape detailed article page for full description
                description = ''
                print(href,'ffffffffffffffffffffffffff')
                headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
    'Accept-Language': 'en-US,en;q=0.5',
    'Connection': 'keep-alive',
}
                if href:
                    resp = requests.get(href, headers=headers, timeout=15)
                    if resp.status_code == 200:
                        article_soup = BeautifulSoup(resp.content, 'html.parser')
                        section_content = article_soup.find(
                            'div',
                            class_='entry-content'
                        )
                        print(section_content)
                        if section_content:
                            paragraphs = section_content.find_all('p', class_="paragraph")
                            description = " ".join([p.text.strip() for p in paragraphs])
                            print(description,'eeeeeeeeeeeeeeeeeeeeeeeeeeeeee')
                # Check for duplicates
                if AllNews.objects.filter(Q(link=href) | Q(title=title)).exists():
                    duplicate_count += 1
                    self.stdout.write(f"Duplicate found: {title}")
                    continue

                # Save English news
                news = AllNews(
                    title=title,
                    slug=slugify(title),
                    discription_main=description,
                    discription='',
                    time=formatted_time,
                    link=href,
                    domain='finbold.com'
                )
                if img:
                    download_and_save_image(news, img)
                news.save()
                saved_count += 1

                # Translate into multiple languages
                for lang in self.LANGS:
                    try:
                        title_trans = translate_to_lang(title, lang)
                        desc_trans = translate_to_lang(description, lang)
                        setattr(news, f"title_{lang}", title_trans)
                        setattr(news, f"discription_{lang}", desc_trans)
                        setattr(news, f"discription_main_{lang}", desc_trans)
                        setattr(news, f"slug_{lang}", slugify(title_trans))
                        time.sleep(0.1)
                    except Exception as e:
                        self.stdout.write(f"[ERROR] Translation failed for {lang} | ID {news.id}: {e}")

                news.save()
                self.stdout.write(f"Saved and translated: {title}")

            except Exception as e:
                self.stdout.write(f"Error processing article: {e}")
                continue

        self.stdout.write(f"Scraping completed. Saved: {saved_count}, Duplicates: {duplicate_count}")
