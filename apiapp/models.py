from django.db import models
from django.utils.text import slugify







class AllNews(models.Model):
    # ✅ Original English fields unchanged
    title = models.TextField()
    slug = models.TextField(blank=True, null=True,unique=False)  # existing field
    link = models.URLField()
    domain = models.TextField()
    image = models.ImageField(upload_to='crptonews-news/')
    time = models.TextField()
    discription = models.TextField(blank=True, default='')
    discription_main = models.TextField(blank=True, default='')
    created_time = models.DateTimeField(auto_now_add=True)
    
    
    LANGS = ['ur', 'ru','ar', 'es', 'fr', 'de', 'zh-cn']
    for lang in LANGS:
        locals()[f"title_{lang}"] = models.TextField( blank=True, null=True)
        locals()[f"discription_{lang}"] = models.TextField(blank=True, default='')
        locals()[f"discription_main_{lang}"] = models.TextField(blank=True, default='')

    def save(self, *args, **kwargs):
        # Auto-generate English slug
        if not self.slug and self.title:
            self.slug = slugify(self.title)

        # Auto-generate slugs for other languages if title exists
        for lang in self.LANGS:
            title_field = f"title_{lang}"
            slug_field = f"slug_{lang}"
            title_value = getattr(self, title_field)
            if title_value and not getattr(self, slug_field):
                setattr(self, slug_field, slugify(title_value))

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
   
from django.db import models
from django.utils.text import slugify

class CoinpediaEvent(models.Model):
    # ✅ Original English Fields
    title = models.TextField( null=True, blank=True)
    date_text = models.TextField( null=True, blank=True)
    location = models.TextField( null=True, blank=True)
    full_url = models.URLField( null=True, blank=True)
    status = models.TextField( default="ongoing") # active, upcoming, ended
    
    # Detail Page Fields
    detail_title = models.TextField( null=True, blank=True)
    detail_location = models.TextField( null=True, blank=True)
    maps_link = models.URLField( null=True, blank=True)
    organized_by = models.TextField( null=True, blank=True)
    website_link = models.URLField( null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    image_src = models.URLField(null=True, blank=True)
    slug = models.SlugField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # ✅ DYNAMIC MULTI-LANGUAGE FIELDS (2026 Advance Version)
    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
    for lang in LANGS:
        locals()[f"title_{lang}"] = models.TextField( blank=True, null=True)
        locals()[f"detail_title_{lang}"] = models.TextField( blank=True, null=True)
        locals()[f"location_{lang}"] = models.TextField( blank=True, null=True)
        locals()[f"detail_location_{lang}"] = models.TextField( blank=True, null=True)
        locals()[f"organized_by_{lang}"] = models.TextField( blank=True, null=True)
        locals()[f"description_{lang}"] = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.title if self.title else "Untitled Event"

    def save(self, *args, **kwargs):
        # Auto-generate English slug for SEO
        if not self.slug and self.title:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)


from django.db import models
from django.utils.text import slugify


class IcoProject(models.Model):

    # ── Core Fields ───────────────────────────────────────────
    name         = models.TextField(help_text="Project name e.g. Katana")
    ticker       = models.CharField(max_length=20,  null=True, blank=True, help_text="Token ticker e.g. KAT")
    project_type = models.TextField(null=True, blank=True, help_text="#230 in Blockchain")
    detail_link  = models.URLField(unique=True)
    slug         = models.SlugField(unique=True, null=True, blank=True)
    status       = models.CharField(max_length=50, default="active", help_text="active / upcoming / ended")

    # ── Time / Status ─────────────────────────────────────────
    status_time  = models.TextField(null=True, blank=True, help_text="e.g. Active 8d left")
    last_updated = models.TextField(null=True, blank=True, help_text="e.g. March 2, 2026, 17:21")  # ✅ NEW

    # ── Images ────────────────────────────────────────────────
    main_img     = models.TextField(null=True, blank=True, help_text="Project avatar/cover image URL")
    footer_img   = models.TextField(null=True, blank=True)

    # ── Financials ────────────────────────────────────────────
    raised_text       = models.TextField(null=True, blank=True, help_text="Total raised display text e.g. $5M or —")
    rounds_count      = models.TextField(null=True, blank=True, help_text="e.g. In 1 rounds")   # ✅ NEW
    pre_valuation     = models.TextField(null=True, blank=True, help_text="Pre-valuation display text")
    investors_summary = models.TextField(null=True, blank=True)

    # ── Detail Fields ─────────────────────────────────────────
    category_name = models.TextField(null=True, blank=True, help_text="e.g. #230 in Blockchain")
    description   = models.TextField(null=True, blank=True)

    # ── Social / Links ────────────────────────────────────────
    website    = models.URLField(null=True, blank=True)
    whitepaper = models.URLField(null=True, blank=True)
    twitter    = models.URLField(null=True, blank=True)
    discord    = models.URLField(null=True, blank=True)   # ✅ NEW
    telegram   = models.URLField(null=True, blank=True)   # ✅ NEW

    # ── Complex JSON Data ─────────────────────────────────────
    # rounds_data: list of round dicts — name, type, status, date, tokens,
    #              platform, platform_url, description, source_url, days_left
    rounds_data   = models.JSONField(default=list)

    # overview_data: total_raised, pre_valuation, rounds_count, last_updated
    overview_data = models.JSONField(default=dict)

    # screenshots: list of {src, name} dicts  — cover + detail images
    screenshots   = models.JSONField(default=list)   # ✅ Properly populated now

    # ── Timestamps ────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ── Dynamic Language Fields ───────────────────────────────
    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
    for lang in LANGS:
        locals()[f"name_{lang}"]         = models.TextField(blank=True, null=True)
        locals()[f"project_type_{lang}"] = models.TextField(blank=True, null=True)
        locals()[f"description_{lang}"]  = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name
    
from django.db import models
from django.db import models
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField # Images upload ke liye

from django.db import models
from django.utils.text import slugify
from ckeditor_uploader.fields import RichTextUploadingField # Assuming you use this

class Article(models.Model):
    # Basic Info
    title = models.TextField( help_text="Article ka catchy title")
    slug = models.SlugField(unique=True, max_length=255, blank=True)
    author = models.CharField(max_length=100, default="Admin")
    
    # Thumbnail Image
    main_image = models.ImageField(upload_to='articles/thumbnails/', help_text="Main hero image")
    
    # Categories
    category = models.CharField(max_length=50, choices=[
        ('news', 'Latest News'),
        ('analysis', 'Technical Analysis'),
        ('prediction', 'Price Prediction'),
        ('guide', 'How-to Guides'),
        ('review', 'Exchange Reviews'),
        ('exchange', 'Exchange'),
        ('ico', 'ICO/IDO News'),
        ('altcoins', 'Altcoin News'),
        ('bitcoin', 'Bitcoin Updates'),
        ('ethereum', 'Ethereum Updates'),
        ('defi', 'DeFi (Decentralized Finance)'),
        ('nft', 'NFTs & Digital Art'),
        ('web3', 'Web3 & Metaverse'),
        ('blockchain', 'Blockchain Technology'),
        ('regulation', 'Legal & Policy'),
        ('mining', 'Crypto Mining'),
        ('security', 'Scams & Security'),
        ('Article', 'Crypto Article'),
    ], default='news')

    # Content (Original English)
    content = RichTextUploadingField(config_name='default')

    # SEO Fields
    meta_description = models.TextField( blank=True, help_text="Google search ke liye choti description")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_published = models.BooleanField(default=True)

    # ✅ DYNAMIC MULTI-LANGUAGE FIELDS (2026 Optimized)
    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
    for lang in LANGS:
        # Title translation
        locals()[f"title_{lang}"] = models.TextField( blank=True, null=True)
        
        # Meta description translation
        locals()[f"meta_description_{lang}"] = models.TextField( blank=True, null=True)
        
        # Article Content translation (Stored as HTML/RichText)
        # Note: We use TextField here to store translated HTML from your AI/Translation script
        locals()[f"content_{lang}"] = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title


from django.db import models
from django.db import models


class WhaleAlert(models.Model):

    # ── Core / Original Fields ─────────────────────────────────────────
    summary          = models.TextField()
    url              = models.URLField(unique=True)
    blockchain       = models.TextField()
    timestamp_text   = models.TextField()          # UTC timestamp from detail page
    transaction_hash = models.CharField(max_length=500, unique=True)
    fee              = models.TextField(null=True, blank=True)   # e.g. "0.000017 ETH"
    asset_price      = models.TextField(null=True, blank=True)   # e.g. "68,123 USD"

    # ── Sender Info ────────────────────────────────────────────────────
    sender_owner         = models.TextField()
    sender_address       = models.TextField()
    sender_amount_crypto = models.TextField()

    # ── Receiver Info ──────────────────────────────────────────────────
    receiver_owner         = models.TextField()
    receiver_address       = models.TextField()
    receiver_amount_crypto = models.TextField()

    # ── NEW: Alert Summary Card Fields ────────────────────────────────
    icon_url          = models.TextField(null=True, blank=True)  # crypto icon path
    amount_full       = models.TextField(null=True, blank=True)  # "67,712,993 #USDC (67,707,238 USD)"
    alert_text        = models.TextField(null=True, blank=True)  # "burned at USDC Treasury"
    alert_timestamp   = models.TextField(null=True, blank=True)  # "6 March 2026 19:41"
    alert_type        = models.TextField(null=True, blank=True)  # "Burn" / "Mint" / "Alert"
    emoticons         = models.TextField(null=True, blank=True)  # "icon-burn, icon-burn"
    social_links      = models.TextField(null=True, blank=True)  # dict as string {twitter:..., telegram:...}

    # ── NEW: Transaction Detail Fields ────────────────────────────────
    timestamp_utc        = models.TextField(null=True, blank=True)  # "Fri, 06 Mar 2026 17:41:35 UTC"
    transaction_hash_url = models.TextField(null=True, blank=True)  # etherscan/explorer link
    fee_usd              = models.TextField(null=True, blank=True)  # "0.03 USD"
    tx_card_title        = models.TextField(null=True, blank=True)  # "Burn" / "Transfer" / "Mint"

    # ── NEW: Sender Extra Fields ───────────────────────────────────────
    sender_address_url  = models.TextField(null=True, blank=True)  # full explorer URL
    sender_amount_usd   = models.TextField(null=True, blank=True)  # USD equivalent

    # ── NEW: Receiver Extra Fields ─────────────────────────────────────
    receiver_address_url  = models.TextField(null=True, blank=True)  # full explorer URL
    receiver_amount_usd   = models.TextField(null=True, blank=True)  # USD equivalent

    # ── Timestamps ─────────────────────────────────────────────────────
    created_at = models.DateTimeField(auto_now_add=True)

    # ── Summary Translations (6 languages) ────────────────────────────
    # Only summary is translated — it's the only human-readable field
    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
    for lang in LANGS:
        locals()[f"summary_{lang}"] = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.blockchain} - {self.transaction_hash}"