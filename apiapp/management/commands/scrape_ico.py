import re
import time
import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apiapp.models import IcoProject
from apiapp.translate_ai import translate_to_lang


class Command(BaseCommand):
    help = 'Scrape full ICO details — all fields from HTML'

    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']

    # ─────────────────────────────────────────────────────────────────────────
    # DETAIL PAGE — sab kuch extract karo ek hi HTML fetch mein
    # ─────────────────────────────────────────────────────────────────────────
    def fetch_description(self, detail_url, headers):
        """
        Ek project ki detail page se yeh sab extract karta hai:
          ticker, category, links, description, financials,
          last_updated, screenshots, rounds_data
        """
        data = {
            "ticker":        None,
            "main_img":      None,   # avatar from detail page header
            "category_name": None,
            "website":       None,
            "whitepaper":    None,
            "twitter":       None,
            "discord":       None,
            "telegram":      None,
            "description":   None,
            "total_raised":  None,
            "pre_valuation": None,
            "rounds_count":  None,
            "last_updated":  None,
            "screenshots":   [],
            "rounds_data":   [],
        }

        try:
            full_url = detail_url if detail_url.startswith('http') else f"https://icodrops.com{detail_url}"
            resp = requests.get(full_url, headers=headers, timeout=15)
            if resp.status_code != 200:
                self.stdout.write(f"[HTTP {resp.status_code}] {full_url}")
                return data

            soup = BeautifulSoup(resp.text, 'html.parser')

            # ── 1. Ticker ─────────────────────────────────────────────────────
            # <span class="Project-Page-Header__ticker">KAT</span>
            ticker_el = soup.select_one('.Project-Page-Header__ticker')
            if ticker_el:
                data["ticker"] = ticker_el.get_text(strip=True)

            # ── 2. Header Avatar Image ─────────────────────────────────────────
            # <img class="... Project-Page-Header__avatar ..." src="...webp">
            avatar_el = soup.select_one('img.Project-Page-Header__avatar')
            if avatar_el:
                data["main_img"] = avatar_el.get('src') or avatar_el.get('data-src')

            # ── 3. Category ───────────────────────────────────────────────────
            # <span class="Capsule-Svg-Icon__name">#230 in Blockchain</span>
            cat_el = soup.select_one('.Capsule-Svg-Icon__name')
            if cat_el:
                data["category_name"] = cat_el.get_text(strip=True)

            # ── 4. Social / External Links ────────────────────────────────────
            # <ul class="Project-Page-Header__links-list">
            #   <li>  <a class="capsule ..." href="...">  <span>Website</span>  </a>  </li>
            for link_el in soup.select('ul.Project-Page-Header__links-list li a.capsule'):
                href = link_el.get('href', '').strip()
                label = link_el.get_text(strip=True).lower()
                if 'website'    in label: data["website"]    = href
                elif 'whitepaper' in label: data["whitepaper"] = href
                elif 'twitter'  in label: data["twitter"]    = href
                elif 'discord'  in label: data["discord"]    = href
                elif 'telegram' in label: data["telegram"]   = href

            # ── 5. Description ────────────────────────────────────────────────
            # <p class="Overview-Section-Description"
            #    x-init="init('Katana is a chain designed...')">
            desc_el = soup.select_one('.Overview-Section-Description')
            if desc_el:
                x_init = desc_el.get('x-init', '')
                # x-init: overviewSectionDescription() + init('...')
                match = re.search(r"init\('(.*?)'\)\s*\"?\s*$", x_init, re.DOTALL)
                if match:
                    data["description"] = (
                        match.group(1)
                        .replace('\\u002D', '-')
                        .replace("\\'", "'")
                        .replace('\\', '')
                        .strip()
                    )
                else:
                    # Fallback: visible text
                    visible = desc_el.select_one('.Overview-Section-Description__text')
                    data["description"] = visible.get_text(strip=True) if visible else desc_el.get_text(strip=True)

            # ── 6. Financials: Total Raised + Pre-Valuation ───────────────────
            # <div class="Overview-Section-Price-Block__box">
            #   <span class="...title">Total Raised</span>
            #   <span class="...value">  <span class="Empty-Data">—</span>  </span>
            #   <span class="...round-text">In 1 rounds</span>
            # </div>
            for box in soup.select('.Overview-Section-Price-Block__box'):
                title_el = box.select_one('.Overview-Section-Price-Block__title')
                if not title_el:
                    continue
                title_txt = title_el.get_text(strip=True).lower()

                val_el   = box.select_one('.Overview-Section-Price-Block__value')
                # Agar Empty-Data span ho to "—", warna actual value
                if val_el:
                    empty = val_el.select_one('.Empty-Data')
                    val_txt = '—' if empty else val_el.get_text(strip=True)
                else:
                    val_txt = None

                if 'total raised' in title_txt:
                    data["total_raised"] = val_txt
                    round_el = box.select_one('.Overview-Section-Price-Block__round-text')
                    if round_el:
                        data["rounds_count"] = round_el.get_text(strip=True)  # "In 1 rounds"

                elif 'pre-valuation' in title_txt:
                    data["pre_valuation"] = val_txt

            # ── 7. Last Updated ───────────────────────────────────────────────
            # <time class="Overview-Section-Info-List__time">March 2, 2026, 17:21</time>
            lu_el = soup.select_one('.Overview-Section-Info-List__time')
            if lu_el:
                data["last_updated"] = lu_el.get_text(strip=True)

            # ── 8. Screenshots ────────────────────────────────────────────────
            # PPT (top section) mein cover + thumbnails:
            # <img class="PPT-Screenshots__cover" src="...cover...webp">
            # <li class="PPT-Screenshots__item"><img src="...screenshot..." alt="..."></li>
            #
            # PD (project details section) mein:
            # <li class="PD-Screenshots__item">
            #   <img data-src="...screenshot..." alt="...">
            #   <span class="PD-Screenshots__name">Katana About</span>
            # </li>
            screenshots = []
            seen_srcs   = set()

            # Cover image
            cover_el = soup.select_one('img.PPT-Screenshots__cover')
            if cover_el:
                src  = cover_el.get('src') or cover_el.get('data-src')
                name = cover_el.get('alt', 'Cover')
                if src and src not in seen_srcs:
                    screenshots.append({"src": src, "name": name, "type": "cover"})
                    seen_srcs.add(src)

            # PD-Screenshots (detail section) — has actual name labels
            for item in soup.select('.PD-Screenshots__item'):
                img_el  = item.select_one('img')
                name_el = item.select_one('.PD-Screenshots__name')
                if img_el:
                    src  = img_el.get('src') or img_el.get('data-src')
                    name = name_el.get_text(strip=True) if name_el else img_el.get('alt', 'Screenshot')
                    if src and src not in seen_srcs:
                        screenshots.append({"src": src, "name": name, "type": "screenshot"})
                        seen_srcs.add(src)

            data["screenshots"] = screenshots

            # ── 9. Rounds Data ────────────────────────────────────────────────
            # PPT-Rounds (top table) se round types collect karo
            # .PPT-Rounds__link-box → .PPT-Rounds__round-name + .PPT-Rounds__round-type
            ppt_types = {}  # { round_name_lower: round_type }
            for ppt_item in soup.select('.PPT-Rounds__link-box'):
                rname_el = ppt_item.select_one('.PPT-Rounds__round-name')
                rtype_el = ppt_item.select_one('.PPT-Rounds__round-type')
                if rname_el and rtype_el:
                    ppt_types[rname_el.get_text(strip=True).lower()] = rtype_el.get_text(strip=True)

            # Detail rounds se baaki sab fields
            rounds = []
            for item in soup.select('.Project-Page-Rounds-List__item'):
                card = item.select_one('.Project-Page-Custom-Card')
                if not card:
                    continue

                r = {}

                # Round name  →  <h2 class="Proj-Rounds-Header__title">
                name_el      = card.select_one('.Proj-Rounds-Header__title')
                r["name"]    = name_el.get_text(strip=True) if name_el else "N/A"

                # Round type — PPT table se match karo
                r["type"]    = ppt_types.get(r["name"].lower(), "N/A")

                # Status  →  <span class="Cpsl-Couple__l-part ...">Active</span>
                status_el    = card.select_one('.Cpsl-Couple__l-part')
                r["status"]  = status_el.get_text(strip=True) if status_el else "N/A"

                # Date range  →  <time class="Cpsl-Couple__r-part">Mar 3 – Mar 17, 2026</time>
                date_el      = card.select_one('time.Cpsl-Couple__r-part')
                r["date"]    = date_el.get_text(strip=True) if date_el else "N/A"

                # Days left  →  <span class="PPT-Rounds__active-date">8 Days left</span>
                days_el      = card.select_one('.PPT-Rounds__active-date')
                r["days_left"] = days_el.get_text(strip=True) if days_el else "N/A"

                # Tokens for round  →  <span class="Rounds-Card-Info-Block__value">50 M KAT</span>
                tokens_el    = card.select_one('.Rounds-Card-Info-Block__value')
                r["tokens"]  = tokens_el.get_text(strip=True) if tokens_el else "N/A"

                # Platform name  →  <span class="Rounds-Card-Info-Block__investor-name">Binance</span>
                platform_el        = card.select_one('.Rounds-Card-Info-Block__investor-name')
                r["platform"]      = platform_el.get_text(strip=True) if platform_el else "N/A"

                # Platform URL  →  <a class="Rounds-Card-Info-Block__top-investor" href="...">
                platform_a         = card.select_one('a.Rounds-Card-Info-Block__top-investor[href]')
                r["platform_url"]  = platform_a.get('href', 'N/A') if platform_a else "N/A"

                # Round description  →  <p class="Project-Page-Custom-Card-Description">...</p>
                desc_el            = card.select_one('.Project-Page-Custom-Card-Description')
                r["description"]   = desc_el.get_text(strip=True) if desc_el else "N/A"

                # Source URL  →  <a class="Project-Page-Custom-Card-Distribution__link" href="...">
                source_el          = card.select_one('.Project-Page-Custom-Card-Distribution__link')
                r["source_url"]    = source_el.get('href', 'N/A') if source_el else "N/A"

                rounds.append(r)

            data["rounds_data"] = rounds

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"[fetch_description error] {e}"))

        return data

    # ─────────────────────────────────────────────────────────────────────────
    # MAIN handle
    # ─────────────────────────────────────────────────────────────────────────
    def handle(self, *args, **options):
        url     = "https://icodrops.com/"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"}

        try:
            resp = requests.get(url, headers=headers, timeout=15)
            soup = BeautifulSoup(resp.text, 'html.parser')
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Main page error: {e}"))
            return

        sections = [
            ('.All-Projects__column--active',   'active'),
            ('.All-Projects__column--upcoming', 'upcoming'),
            ('.All-Projects__column--ended',    'ended'),
        ]

        total_saved = 0
        limit       = 10   # ← adjust as needed

        for selector, status_label in sections:
            if total_saved >= limit:
                break

            column = soup.select_one(selector)
            if not column:
                continue

            for card in column.select('.Project-Card'):
                if total_saved >= limit:
                    break

                # ── detail link ──────────────────────────────────────────────
                parent_a    = card.find_parent('a', class_='All-Projects__item')
                detail_link = parent_a.get('href', '').strip() if parent_a else ''
                if not detail_link:
                    continue

                # ── duplicate check ──────────────────────────────────────────
                if IcoProject.objects.filter(detail_link=detail_link).exists():
                    self.stdout.write(f"[SKIP] {detail_link}")
                    continue

                # ── card-level fields ─────────────────────────────────────────
                # Name  →  <span class="Project-Card__name">Katana</span>
                name_el = card.select_one('.Project-Card__name')
                name    = name_el.get_text(strip=True) if name_el else "N/A"
                # strip ticker text that might be inside the span
                abbr_el = card.select_one('.Project-Card__ticker')
                if abbr_el:
                    name = name.replace(abbr_el.get_text(strip=True), '').strip()

                # Ticker  →  <abbr class="Project-Card__ticker" title="Katana">KAT</abbr>
                ticker_card = abbr_el.get('title', '').strip() if abbr_el else None

                # Project type  →  <div class="Project-Card__type">#230 in Blockchain / ...</div>
                type_el      = card.select_one('.Project-Card__type')
                project_type = type_el.get_text(strip=True) if type_el else None

                # Status time  →  <time class="Cpsl-Platform-Time__time">Active 8d left</time>
                time_el     = card.select_one('.Cpsl-Platform-Time__time')
                status_time = time_el.get_text(strip=True) if time_el else None

                # Card thumbnail image  →  <img class="Avt ... Project-Card__avt" src="...">
                img_el    = card.select_one('img.Project-Card__avt')
                card_img  = None
                if img_el:
                    card_img = img_el.get('src') or img_el.get('data-src')

                # ── deep fetch ────────────────────────────────────────────────
                self.stdout.write(f"→ Fetching: {name}  ({detail_link})")
                detail = self.fetch_description(detail_link, headers)

                # Prefer detail page avatar; fallback to card thumbnail
                main_img = detail["main_img"] or card_img

                # ── overview_data dict ────────────────────────────────────────
                overview_data = {
                    "total_raised":  detail["total_raised"],
                    "pre_valuation": detail["pre_valuation"],
                    "rounds_count":  detail["rounds_count"],
                    "last_updated":  detail["last_updated"],
                }

                # ── save to DB ────────────────────────────────────────────────
                project = IcoProject.objects.create(
                    name             = name,
                    ticker           = detail["ticker"] or ticker_card,
                    project_type     = project_type,
                    status           = status_label,
                    status_time      = status_time,
                    detail_link      = detail_link,
                    main_img         = main_img,
                    description      = detail["description"],
                    category_name    = detail["category_name"],
                    website          = detail["website"],
                    whitepaper       = detail["whitepaper"],
                    twitter          = detail["twitter"],
                    discord          = detail["discord"],
                    telegram         = detail["telegram"],
                    raised_text      = detail["total_raised"],
                    rounds_count     = detail["rounds_count"],
                    pre_valuation    = detail["pre_valuation"],
                    last_updated     = detail["last_updated"],
                    investors_summary= f"Rounds: {detail['rounds_count']} | Valuation: {detail['pre_valuation']}",
                    rounds_data      = detail["rounds_data"],
                    overview_data    = overview_data,
                    screenshots      = detail["screenshots"],
                )
                total_saved += 1

                # ── translations ──────────────────────────────────────────────
                for lang in self.LANGS:
                    try:
                        if name and name != "N/A":
                            setattr(project, f"name_{lang}", translate_to_lang(name, lang))
                            time.sleep(0.1)
                    except Exception as e:
                        self.stdout.write(f"[Trans name/{lang}] {e}")

                    try:
                        desc = detail["description"]
                        if desc:
                            setattr(project, f"description_{lang}", translate_to_lang(desc[:1000], lang))
                            time.sleep(0.1)
                    except Exception as e:
                        self.stdout.write(f"[Trans desc/{lang}] {e}")

                    try:
                        if project_type:
                            setattr(project, f"project_type_{lang}", translate_to_lang(project_type, lang))
                            time.sleep(0.1)
                    except Exception as e:
                        self.stdout.write(f"[Trans type/{lang}] {e}")

                project.save()
                self.stdout.write(self.style.SUCCESS(f"✅ Saved: {name} ({status_label})"))
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS(f"\nDone. Total saved: {total_saved}"))