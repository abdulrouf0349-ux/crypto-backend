from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apiapp.models import AllNews
import time
from django.utils.text import slugify

from apiapp.translate_ai import translate_to_lang  # function to translate text to given lang code


class Command(BaseCommand):
    help = "Translate all English news into multiple languages using Google Translate (robust batch version)"

    LANGS = ["ur", "ru", "es", "fr", "de", "zh-cn"]

    BATCH_SIZE = 50  # number of articles processed per batch
    RETRY_COUNT = 3  # number of retry attempts for failed translations

    def handle(self, *args, **kwargs):
        articles = AllNews.objects.all()
        total = articles.count()
        self.stdout.write(self.style.WARNING(f"Total news articles: {total}"))

        start = 0
        while start < total:
            batch_articles = articles[start:start + self.BATCH_SIZE]
            self.stdout.write(self.style.NOTICE(f"Processing batch {start}-{start + len(batch_articles)}"))
            
            for article in batch_articles:
                if not article.title:
                    self.stdout.write(self.style.WARNING(f"Skipping ID {article.id} → missing title"))
                    continue

                updated = False
                for lang in self.LANGS:
                    title_field = f"title_{lang}"
                    desc_field = f"discription_{lang}"
                    desc_main_field = f"discription_main_{lang}"
                    slug_field = f"slug_{lang}"

                    # Already translated?
                    if getattr(article, title_field):
                        continue

                    # Retry logic
                    for attempt in range(1, self.RETRY_COUNT + 1):
                        try:
                            # Translate title
                            translated_title = translate_to_lang(article.title, lang)

                            # Translate descriptions
                            desc = article.discription or ""
                            desc_main = article.discription_main or ""

                            if desc == desc_main:
                                t_desc = translate_to_lang(desc, lang)
                                t_desc_main = t_desc
                            else:
                                t_desc = translate_to_lang(desc, lang) if desc else ""
                                t_desc_main = translate_to_lang(desc_main, lang) if desc_main else ""

                            # Set translated fields
                            setattr(article, title_field, translated_title)
                            setattr(article, desc_field, t_desc)
                            setattr(article, desc_main_field, t_desc_main)
                            setattr(article, slug_field, slugify(translated_title))

                            updated = True
                            self.stdout.write(self.style.SUCCESS(f"ID {article.id} → translated to {lang}"))
                            break  # break retry loop if successful
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f"[ERROR] ID {article.id} lang {lang} attempt {attempt}: {e}"))
                            time.sleep(1)  # small delay before retry

                # Save article if updated
                if updated:
                    try:
                        article.save()
                        self.stdout.write(self.style.SUCCESS(f"Saved article {article.id}"))
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"[ERROR] Saving ID {article.id}: {e}"))

            start += self.BATCH_SIZE
            self.stdout.write(self.style.NOTICE(f"Finished batch up to article {start}"))
            time.sleep(0.5)  # small delay between batches
