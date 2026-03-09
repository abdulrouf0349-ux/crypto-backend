# from django.core.management.base import BaseCommand
# from playwright.sync_api import sync_playwright
# from apiapp.models import WhaleAlert 
# from apiapp.translate_ai import translate_to_lang  # Translation Import
# import time
# import os

# class Command(BaseCommand):
#     help = 'Scrapes Whale Alert and saves unique records to the database'

#     def handle(self, *args, **options):
#         os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
#         self.scrape_whale_complete()

#     def scrape_whale_complete(self):
#         with sync_playwright() as p:
#             browser = p.chromium.launch(headless=True)
#             context = browser.new_context(
#                 user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
#             )
#             page = context.new_page()
#             page.set_default_timeout(60000)

#             try:
#                 self.stdout.write("Connecting to Whale Alert...")
#                 response = page.goto('https://whale-alert.io/alerts.html', wait_until='commit')
                
#                 if response.status == 403:
#                     self.stdout.write(self.style.ERROR("Blocked by 403 Forbidden."))
#                     return

#                 page.wait_for_selector('#table.table-centered.table-hover.mb-0 tbody tr', timeout=30000)

#                 for i in range(10):
#                     rows = page.locator('##table.table-centered.table-hover.mb-0 tbody tr')
#                     if rows.count() <= i: break
                    
#                     row = rows.nth(i)
                    
#                     # Capture main summary line
#                     amount_summary = row.locator('.recent-alerts-amount').inner_text().strip()
#                     text_summary = row.locator('.alerts-text').inner_text().strip()
#                     full_summary = f"{amount_summary} {text_summary}"
                    
#                     # --- CLICK TO GET DETAILS ---
#                     row.click()
                    
#                     try:
#                         page.wait_for_selector('.card', timeout=10000)
#                     except:
#                         page.go_back()
#                         page.wait_for_selector('#alerts tbody tr')
#                         continue

#                     def get_text_safe(selector):
#                         try:
#                             loc = page.locator(selector)
#                             return loc.first.inner_text().strip() if loc.count() > 0 else "N/A"
#                         except: return "N/A"

#                     # Data Extraction
#                     current_url = page.url
#                     tx_hash = get_text_safe('.tx-hash a')

#                     # --- DUPLICATE CHECK ---
#                     if WhaleAlert.objects.filter(transaction_hash=tx_hash).exists() or WhaleAlert.objects.filter(url=current_url).exists():
#                         self.stdout.write(self.style.WARNING(f"Skipping Duplicate: {tx_hash}"))
#                     else:
#                         blockchain = get_text_safe('.tx-details-blockchain')
#                         timestamp = get_text_safe('.tx-details-timestamp')
#                         fee = get_text_safe('div.tx-title:has-text("Fee") + div')
#                         asset_price = get_text_safe('div.tx-title:has-text("Price") + div')
#                         s_owner = get_text_safe('#from-addresses .tx-owner')
#                         s_addr = get_text_safe('#from-addresses .tx-address a')
#                         s_crypto = get_text_safe('#from-addresses td[style*="text-align: right"]')
#                         r_owner = get_text_safe('#to-addresses .tx-owner')
#                         r_addr = get_text_safe('#to-addresses .tx-address a')
#                         r_crypto = get_text_safe('#to-addresses td[style*="text-align: right"]')

#                         # --- SAVE TO DATABASE ---
#                         whale_obj = WhaleAlert.objects.create(
#                             summary=full_summary,
#                             url=current_url,
#                             blockchain=blockchain,
#                             timestamp_text=timestamp,
#                             transaction_hash=tx_hash,
#                             fee=fee.splitlines()[0] if 'N/A' not in fee else 'N/A',
#                             asset_price=asset_price.splitlines()[0] if 'N/A' not in asset_price else 'N/A',
#                             sender_owner=s_owner if s_owner else 'Private Wallet',
#                             sender_address=s_addr,
#                             sender_amount_crypto=s_crypto.replace('   ', ' '),
#                             receiver_owner=r_owner if r_owner else 'Private Wallet',
#                             receiver_address=r_addr,
#                             receiver_amount_crypto=r_crypto.replace('   ', ' ')
#                         )

#                         # ✅ ADDED: TRANSLATION LOGIC FOR SUMMARY
#                         LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
#                         for lang in LANGS:
#                             try:
#                                 translated_summary = translate_to_lang(full_summary, lang)
#                                 setattr(whale_obj, f"summary_{lang}", translated_summary)
#                                 time.sleep(0.1)
#                             except Exception as e:
#                                 self.stdout.write(f"Translation Error for {lang}: {e}")
                        
#                         whale_obj.save() # Final Save after translations
#                         self.stdout.write(self.style.SUCCESS(f"Saved & Translated: {tx_hash}"))

#                     # Return and wait
#                     time.sleep(1)
#                     page.go_back()
#                     page.wait_for_selector('#alerts tbody tr')

#             except Exception as e:
#                 self.stdout.write(self.style.ERROR(f"Error: {e}"))
#             finally:
#                 browser.close()



from django.core.management.base import BaseCommand
from playwright.sync_api import sync_playwright
from apiapp.models import WhaleAlert
from apiapp.translate_ai import translate_to_lang
import time
import os


class Command(BaseCommand):
    help = 'Scrapes Whale Alert list + detail pages, saves all fields to DB'

    def handle(self, *args, **options):
        os.environ["DJANGO_ALLOW_ASYNC_UNSAFE"] = "true"
        self.scrape_whale_complete()

    # ─────────────────────────────────────────────────────────────────────
    #  scrape_detail_page()
    #  Call this AFTER page.goto(detail_url) is done.
    #  Returns a dict of every field extracted from the detail page HTML,
    #  or None if the page failed to load.
    #
    #  Detail URL format:
    #    https://whale-alert.io/transaction/ethereum/0xABC...
    # ─────────────────────────────────────────────────────────────────────
    def scrape_detail_page(self, page):

        # ── Tiny helpers ──────────────────────────────────────────────
        def get_text(selector):
            try:
                loc = page.locator(selector)
                return loc.first.inner_text().strip() if loc.count() > 0 else "N/A"
            except:
                return "N/A"

        def get_attr(selector, attr):
            try:
                loc = page.locator(selector)
                val = loc.first.get_attribute(attr)
                return val.strip() if val else "N/A"
            except:
                return "N/A"

        # Wait for at least one .card to appear
        try:
            page.wait_for_selector('.card', timeout=15000)
        except:
            return None

        current_url = page.url

        # ══════════════════════════════════════════════════════════════
        #  1.  ALERT SUMMARY CARD  (table#alerts)
        # ══════════════════════════════════════════════════════════════

        # Crypto icon URL  — extracted from inline style background-image
        icon_style = get_attr('table#alerts .alerts-icon', 'style')
        icon_url = "N/A"
        if 'url(' in icon_style:
            try:
                icon_url = (
                    icon_style
                    .split('url(')[1]
                    .split(')')[0]
                    .strip().strip('"').strip("'")
                    .replace(' !important', '')
                )
            except:
                pass

        # Amount + USD  e.g. "67,712,993 #USDC (67,707,238 USD)"
        amount_full = get_text('table#alerts .alerts-amount')

        # Alert text  e.g. "burned at USDC Treasury"
        alert_text = get_text('table#alerts .alerts-text').strip()

        # Datetime shown in summary card  e.g. "6 March 2026 19:41"
        alert_timestamp_display = get_text('table#alerts .alerts-ago')

        # Alert type + emoticons
        emoticon_icons = page.locator('table#alerts .alerts-emoticons i')
        icon_classes = []
        for j in range(emoticon_icons.count()):
            cls = emoticon_icons.nth(j).get_attribute('class') or ''
            icon_classes.append(cls.strip())
        alert_type = "N/A"
        if icon_classes:
            alert_type = icon_classes[0].replace('icon-', '').capitalize()  # Burn/Mint/Alert
        emoticons_str = ', '.join(set(icon_classes))

        # Social share links (X / Telegram / Discord / Bluesky)
        social_links = {}
        for name, pattern in [
            ('twitter',  'twitter.com'),
            ('telegram', 't.me'),
            ('discord',  'discord.com'),
            ('bluesky',  'bsky.app'),
        ]:
            href = get_attr(f'.view-on a[href*="{pattern}"]', 'href')
            if href != "N/A":
                social_links[name] = href

        # ══════════════════════════════════════════════════════════════
        #  2.  TRANSACTION DETAILS CARD  (.tx-header)
        # ══════════════════════════════════════════════════════════════

        # Blockchain  e.g. "Ethereum"
        blockchain_raw = get_text('.tx-details-blockchain')
        blockchain = blockchain_raw.split()[0] if blockchain_raw != "N/A" else "N/A"

        # Timestamp UTC  e.g. "Fri, 06 Mar 2026 17:41:35 UTC"
        timestamp_utc = get_text('.tx-details-timestamp').strip('()')

        # Transaction hash (link text)
        tx_hash = get_text('.tx-hash a')

        # Transaction hash explorer URL  e.g. "https://etherscan.io/tx/0x..."
        tx_hash_url = get_attr('.tx-hash a', 'href')

        # Fee  — find the row containing "Fee" text, grab the col-md-9 value
        fee_text = "N/A"
        fee_usd  = "N/A"
        fee_rows = page.locator('.tx-header .row')
        for k in range(fee_rows.count()):
            row_text = fee_rows.nth(k).inner_text()
            if 'Fee' in row_text:
                col = fee_rows.nth(k).locator('.col-md-9')
                if col.count() > 0:
                    fee_text = col.first.inner_text().strip().splitlines()[0].strip()
                # USD fee is stored in data-bs-title of the info icon
                info = fee_rows.nth(k).locator('[data-bs-title]')
                if info.count() > 0:
                    fee_usd = info.first.get_attribute('data-bs-title') or "N/A"
                break

        # ══════════════════════════════════════════════════════════════
        #  3.  TX TYPE CARD TITLE  e.g. "Burn", "Transfer", "Mint"
        # ══════════════════════════════════════════════════════════════
        tx_card_title = get_text('.tx-card .header-title')

        # ══════════════════════════════════════════════════════════════
        #  4.  SENDER  (#from-addresses)
        # ══════════════════════════════════════════════════════════════
        sender_address_url = get_attr('#from-addresses .tx-address a', 'href')
        sender_address     = sender_address_url.split('/')[-1] if sender_address_url != "N/A" else "N/A"
        sender_owner       = get_text('#from-addresses .tx-owner') or "Private Wallet"

        # Crypto amount is in the right-aligned td; USD amount is in .tx-amount inside same td
        sender_td_raw      = get_text('#from-addresses td[style*="text-align: right"]')
        sender_td_lines    = [l.strip() for l in sender_td_raw.splitlines() if l.strip()]
        sender_amount_crypto = sender_td_lines[0] if sender_td_lines else "N/A"
        sender_amount_usd    = get_text('#from-addresses .tx-amount')

        # ══════════════════════════════════════════════════════════════
        #  5.  RECEIVER  (#to-addresses)
        # ══════════════════════════════════════════════════════════════
        receiver_address_url = get_attr('#to-addresses .tx-address a', 'href')
        receiver_address     = receiver_address_url.split('/')[-1] if receiver_address_url != "N/A" else "N/A"
        receiver_owner       = get_text('#to-addresses .tx-owner') or "Private Wallet"

        receiver_td_raw      = get_text('#to-addresses td[style*="text-align: right"]')
        receiver_td_lines    = [l.strip() for l in receiver_td_raw.splitlines() if l.strip()]
        receiver_amount_crypto = receiver_td_lines[0] if receiver_td_lines else "N/A"
        receiver_amount_usd    = get_text('#to-addresses .tx-amount')

        # ══════════════════════════════════════════════════════════════
        #  6.  COMBINED SUMMARY
        # ══════════════════════════════════════════════════════════════
        full_summary = f"{amount_full} {alert_text}"

        return {
            # Alert card
            'url':                    current_url,
            'icon_url':               icon_url,
            'amount_full':            amount_full,
            'alert_text':             alert_text,
            'alert_timestamp':        alert_timestamp_display,
            'alert_type':             alert_type,
            'emoticons':              emoticons_str,
            'social_links':           str(social_links),

            # Transaction details
            'blockchain':             blockchain,
            'timestamp_utc':          timestamp_utc,
            'transaction_hash':       tx_hash,
            'transaction_hash_url':   tx_hash_url,
            'fee':                    fee_text,
            'fee_usd':                fee_usd,
            'tx_card_title':          tx_card_title,

            # Sender
            'sender_address':         sender_address,
            'sender_address_url':     sender_address_url,
            'sender_owner':           sender_owner,
            'sender_amount_crypto':   sender_amount_crypto,
            'sender_amount_usd':      sender_amount_usd,

            # Receiver
            'receiver_address':       receiver_address,
            'receiver_address_url':   receiver_address_url,
            'receiver_owner':         receiver_owner,
            'receiver_amount_crypto': receiver_amount_crypto,
            'receiver_amount_usd':    receiver_amount_usd,

            # Derived
            'summary':                full_summary,
        }

    # ─────────────────────────────────────────────────────────────────────
    #  MAIN SCRAPER
    # ─────────────────────────────────────────────────────────────────────
    def scrape_whale_complete(self):
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
            )
            page = context.new_page()
            page.set_default_timeout(60000)

            try:
                self.stdout.write("Connecting to Whale Alert list page...")
                response = page.goto('https://whale-alert.io/', wait_until='commit')

                if response and response.status == 403:
                    self.stdout.write(self.style.ERROR("Blocked by 403 Forbidden."))
                    return

                page.wait_for_selector('table#recent-alerts tbody tr', timeout=30000)
                self.stdout.write(self.style.SUCCESS("List page loaded."))

                rows = page.locator('table#recent-alerts tbody tr')
                total_rows = rows.count()
                self.stdout.write(f"Found {total_rows} rows on list page.")

                # ── Step 1: Collect all detail page URLs by clicking each row ──
                detail_urls = []
                for i in range(total_rows):
                    try:
                        row = page.locator('table#recent-alerts tbody tr').nth(i)
                        row.click()
                        page.wait_for_load_state('domcontentloaded', timeout=10000)
                        detail_url = page.url
                        if '/transaction/' in detail_url:
                            detail_urls.append(detail_url)
                            self.stdout.write(f"  [{i+1}] {detail_url}")
                        page.go_back()
                        page.wait_for_selector('table#recent-alerts tbody tr', timeout=15000)
                        time.sleep(0.5)
                    except Exception as e:
                        self.stdout.write(self.style.WARNING(f"  Row {i} click error: {e}"))
                        try:
                            page.go_back()
                            page.wait_for_selector('table#recent-alerts tbody tr', timeout=15000)
                        except:
                            pass

                self.stdout.write(f"\nCollected {len(detail_urls)} detail URLs. Starting detail scrape...\n")

                # ── Step 2: Visit each detail URL and scrape all data ──────────
                for detail_url in detail_urls:

                    # Duplicate check by URL
                    if WhaleAlert.objects.filter(url=detail_url).exists():
                        self.stdout.write(self.style.WARNING(f"Duplicate URL, skipping: {detail_url}"))
                        continue

                    try:
                        page.goto(detail_url, wait_until='domcontentloaded')
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f"Failed to load {detail_url}: {e}"))
                        continue

                    data = self.scrape_detail_page(page)

                    if data is None:
                        self.stdout.write(self.style.WARNING(f"No data from {detail_url}, skipping."))
                        continue

                    # Duplicate check by tx hash
                    if (data['transaction_hash'] != 'N/A' and
                            WhaleAlert.objects.filter(transaction_hash=data['transaction_hash']).exists()):
                        self.stdout.write(self.style.WARNING(
                            f"Duplicate hash {data['transaction_hash'][:20]}..., skipping."
                        ))
                        continue

                    # ── Save all fields to DB ──────────────────────────────────
                    whale_obj = WhaleAlert.objects.create(
                        # Alert card
                        summary=data['summary'],
                        url=data['url'],
                        icon_url=data['icon_url'],
                        amount_full=data['amount_full'],
                        alert_text=data['alert_text'],
                        alert_timestamp=data['alert_timestamp'],
                        alert_type=data['alert_type'],
                        emoticons=data['emoticons'],
                        social_links=data['social_links'],

                        # Transaction details
                        blockchain=data['blockchain'],
                        timestamp_utc=data['timestamp_utc'],
                        transaction_hash=data['transaction_hash'],
                        transaction_hash_url=data['transaction_hash_url'],
                        fee=data['fee'],
                        fee_usd=data['fee_usd'],
                        tx_card_title=data['tx_card_title'],

                        # Sender
                        sender_address=data['sender_address'],
                        sender_address_url=data['sender_address_url'],
                        sender_owner=data['sender_owner'],
                        sender_amount_crypto=data['sender_amount_crypto'],
                        sender_amount_usd=data['sender_amount_usd'],

                        # Receiver
                        receiver_address=data['receiver_address'],
                        receiver_address_url=data['receiver_address_url'],
                        receiver_owner=data['receiver_owner'],
                        receiver_amount_crypto=data['receiver_amount_crypto'],
                        receiver_amount_usd=data['receiver_amount_usd'],
                    )

                    # ── Translations for summary ───────────────────────────────
                    LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
                    for lang in LANGS:
                        try:
                            translated = translate_to_lang(data['summary'], lang)
                            setattr(whale_obj, f"summary_{lang}", translated)
                            time.sleep(0.1)
                        except Exception as e:
                            self.stdout.write(f"  Translation error [{lang}]: {e}")

                    whale_obj.save()
                    self.stdout.write(self.style.SUCCESS(
                        f"✅ Saved: {data['transaction_hash'][:20]}... | {data['summary'][:60]}"
                    ))
                    time.sleep(1)

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"Fatal error: {e}"))
            finally:
                browser.close()