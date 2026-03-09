# admin.py
from django.contrib import admin
from django.utils.text import slugify
from .models import Article
from .translate_ai import translate_to_lang  # your existing translate wrapper
import time


# ─────────────────────────────────────────────────────────────
# Helper: Translate all language fields for an Article instance
# ─────────────────────────────────────────────────────────────
LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

def run_translations(article):
    """
    Translates title, meta_description, and content into all LANGS.
    Skips a field if translation already exists (to avoid re-translating on every save).
    """
    for lang in LANGS:
        try:
            # ── Title ──────────────────────────────────────────
            existing_title = getattr(article, f"title_{lang}", None)
            if not existing_title and article.title:
                translated_title = translate_to_lang(article.title, lang)
                setattr(article, f"title_{lang}", translated_title)
                # Auto slug for this language
                setattr(article, f"slug_{lang}", slugify(translated_title)) if hasattr(article, f"slug_{lang}") else None
                time.sleep(0.1)

            # ── Meta Description ───────────────────────────────
            existing_meta = getattr(article, f"meta_description_{lang}", None)
            if not existing_meta and article.meta_description:
                translated_meta = translate_to_lang(article.meta_description, lang)
                setattr(article, f"meta_description_{lang}", translated_meta)
                time.sleep(0.1)

            # ── Content ────────────────────────────────────────
            existing_content = getattr(article, f"content_{lang}", None)
            if not existing_content and article.content:
                translated_content = translate_to_lang(article.content, lang)
                setattr(article, f"content_{lang}", translated_content)
                time.sleep(0.1)

        except Exception as e:
            print(f"[Translation ERROR] lang={lang} | article_id={article.id} | {e}")
            continue


# ─────────────────────────────────────────────────────────────
# Custom ModelAdmin
# ─────────────────────────────────────────────────────────────
@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):

    # ── List View ──────────────────────────────────────────────
    list_display  = ('title', 'category', 'author', 'is_published', 'created_at', 'translation_status')
    list_filter   = ('category', 'is_published', 'created_at')
    search_fields = ('title', 'author', 'slug')
    list_editable = ('is_published',)
    ordering      = ('-created_at',)
    date_hierarchy = 'created_at'

    # ── Slug auto-fill from title (JS) ────────────────────────
    prepopulated_fields = {'slug': ('title',)}

    # ── Read-only ─────────────────────────────────────────────
    readonly_fields = ('created_at', 'updated_at', 'translation_status')

    # ── Fieldsets — Admin form layout ─────────────────────────
    fieldsets = (
        ('📝 Basic Info', {
            'fields': ('title', 'slug', 'author', 'category', 'main_image', 'is_published')
        }),
        ('📄 Content', {
            'fields': ('content',)
        }),
        ('🔍 SEO', {
            'fields': ('meta_description',),
            'description': 'Save karne ke baad translations automatic generate honge.'
        }),
        ('🌐 Translation Status', {
            'fields': ('translation_status',),
            'classes': ('collapse',),
        }),
        ('🕒 Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    # ── Translation status display ─────────────────────────────
    def translation_status(self, obj):
        if not obj.pk:
            return "Save karne ke baad translations generate honge."
        status_parts = []
        for lang in LANGS:
            title_val = getattr(obj, f"title_{lang}", None)
            icon = "✅" if title_val else "⏳"
            status_parts.append(f"{icon} {lang.upper()}")
        return "  |  ".join(status_parts)

    translation_status.short_description = "Translation Status"

    # ── Core: save_model — yahan auto-translate hota hai ──────
    def save_model(self, request, obj, form, change):
        """
        1. Slug auto-generate karo (agar blank hai)
        2. Pehle object save karo (ID chahiye translations ke liye)
        3. Translations run karo
        4. Final save karo translations ke saath
        """

        # Step 1: Slug
        if not obj.slug:
            obj.slug = slugify(obj.title)

        # Step 2: Pehla save (ID generate karne ke liye)
        super().save_model(request, obj, form, change)

        # Step 3: Translations (sirf naye articles ya force-retranslate)
        # Agar title change hua hai to re-translate (change=True means update)
        needs_translation = (
            not change  # Naya article
            or 'title' in form.changed_data          # Title badla
            or 'content' in form.changed_data        # Content badla
            or 'meta_description' in form.changed_data  # Meta badli
        )

        if needs_translation:
            # Agar title change hua to purani translations clear karo
            if change and 'title' in form.changed_data:
                for lang in LANGS:
                    setattr(obj, f"title_{lang}", None)

            if change and 'content' in form.changed_data:
                for lang in LANGS:
                    setattr(obj, f"content_{lang}", None)

            if change and 'meta_description' in form.changed_data:
                for lang in LANGS:
                    setattr(obj, f"meta_description_{lang}", None)

            # Translations run karo
            self.message_user(
                request,
                f"'{obj.title}' ke liye {len(LANGS)} languages mein translation shuru ho gai...",
                level='INFO'
            )
            run_translations(obj)

            # Step 4: Final save with translations
            obj.save()

            self.message_user(
                request,
                f"✅ '{obj.title}' successfully save aur {len(LANGS)} languages mein translate ho gaya!",
                level='SUCCESS'
            )
        else:
            self.message_user(
                request,
                f"✅ '{obj.title}' saved. (Translations unchanged)",
                level='SUCCESS'
            )