from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from apiapp.models import AllNews
from django.db.models import Q
from django.core.files import File
from django.utils.text import slugify
from io import BytesIO
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
    help = 'Scrapes news from DailyHodl and translates into multiple languages'

    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

    def handle(self, *args, **kwargs):
        response = requests.get('https://dailyhodl.com/news/')
        if response.status_code != 200:
            self.stdout.write(f"Error fetching website: {response.status_code}")
            return

        soup = BeautifulSoup(response.content, 'html.parser')
        section = soup.find('div', class_="jeg_posts jeg_load_more_flag")
        section_Div = section.find_all('article') if section else []

        saved_count = 0
        duplicate_count = 0

        for d in section_Div[:5]:  # Limit to 5 articles
            try:
                div_2 = d.find('div', class_='jeg_thumb')
                a_Tag = div_2.find('a') if div_2 else None
                href = a_Tag.get('href') if a_Tag else None

                img_tag = a_Tag.find('img') if a_Tag else None
                img = img_tag.get('src') if img_tag else None
                base_img_url = img.split('?')[0] if img else None

                title1 = d.find('div', class_='jeg_postblock_content')
                title2 = title1.find('a') if title1 else None
                titleee = title2.text.strip() if title2 else "No title"
                title = titleee.strip('"').strip("'")

                title3 = title1.find('div', class_='jeg_post_meta') if title1 else None
                title4 = title3.find('div', class_='jeg_meta_date') if title3 else None
                discrition = title1.find('div', class_='jeg_post_excerpt') if title1 else None

                time_text = title4.text.strip() if title4 else "No time"
                date_format = "%B %d, %Y"
                dt = datetime.strptime(time_text, date_format) if time_text != "No time" else datetime.now()
                dt_with_time = dt.replace(hour=0, minute=0, second=0, microsecond=47071)

                short_disc__ = discrition.find('p') if discrition else None
                short_disc = short_disc__.text.strip() if short_disc__ else "No description"

                # Scrape detailed article page
                article_description = ''
                if href:
                    article_resp = requests.get(href)
                    if article_resp.status_code == 200:
                        article_soup = BeautifulSoup(article_resp.content, 'html.parser')
                        content_section = article_soup.find('div', class_='content-inner')
                        if content_section:
                            paragraphs = content_section.find_all('p')
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
                    discription='',
                    discription_main=article_description,
                    time=dt_with_time,
                    link=href,
                    domain='dailyhodl.com'
                )
                if base_img_url:
                    download_and_save_image(news, base_img_url)
                news.save()
                saved_count += 1

                # Translate into multiple languages
                for lang in self.LANGS:
                    try:
                        title_trans = translate_to_lang(title, lang)
                        desc_trans = translate_to_lang(article_description, lang)
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
