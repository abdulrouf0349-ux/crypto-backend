import asyncio
from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
from apiapp.models import CoinpediaEvent 
from django.db.models import Q # Duplicate check ke liye

import asyncio
import time # Sleep ke liye
from django.core.management.base import BaseCommand
from playwright.async_api import async_playwright
from asgiref.sync import sync_to_async
from apiapp.models import CoinpediaEvent 
from django.db.models import Q 
from apiapp.translate_ai import translate_to_lang # Aapka translation function

@sync_to_async
def save_event(data):
    title = data.get('anchor_text', '')
    description = data.get('full_desc', '')
    url = data['full_url']
    location = data.get('location', '')
    organized_by = data.get('organized_by', '')

    # --- Duplicate Check Logic ---
    exists = CoinpediaEvent.objects.filter(
        Q(full_url=url) | 
        Q(title=title, description=description)
    ).exists()

    if not exists:
        # 1. English Data Save Karein
        event_obj = CoinpediaEvent.objects.create(
            full_url=url,
            title=title,
            image_src=data.get('image_src', ''),
            description=description,
            detail_title=data.get('disc_title', ''),
            detail_location=data.get('disc_location', ''),
            location=location,
            date_text=data.get('date_text', ''),
            maps_link=data.get('location_href', ''),
            website_link=data.get('website_link', ''),
            organized_by=organized_by,
            status=data.get('status', '')
        )

        # 2. ✅ Translation Logic (Same as AllNews Sample)
        LANGS = ['ur', 'ru', 'es', 'fr', 'de', 'zh-cn']
        
        for lang in LANGS:
            try:
                # Title, Description, aur Location translate karein
                t_title = translate_to_lang(title, lang)
                t_desc = translate_to_lang(description, lang)
                t_loc = translate_to_lang(location, lang)
                t_org = translate_to_lang(organized_by, lang)

                # Dynamic fields set karein
                setattr(event_obj, f"title_{lang}", t_title)
                setattr(event_obj, f"description_{lang}", t_desc)
                setattr(event_obj, f"location_{lang}", t_loc)
                setattr(event_obj, f"detail_title_{lang}", t_title) # Detail title same as title
                setattr(event_obj, f"detail_location_{lang}", t_loc)
                setattr(event_obj, f"organized_by_{lang}", t_org)

                time.sleep(0.1) # AI API par load kam karne ke liye
            except Exception as e:
                print(f"[ERROR] Translation failed for {lang} | Event ID {event_obj.id}: {e}")

        # Final Save with translations
        event_obj.save()
        return True 
    else:
        print(f"Skipping Duplicate: {title[:30]}...")
        return False
async def get_full_description(browser_context, event_url):
    domain = "https://events.coinpedia.org"
    full_link = f"{domain}{event_url}" if event_url.startswith('/') else event_url
    page = await browser_context.new_page()
    description, disc_title, disc_location, location_href, website_link, organized_by = "", "", "", "", "", ""
    try:
        await page.goto(full_link, wait_until="domcontentloaded", timeout=30000)
        await asyncio.sleep(1) 
        grid = await page.query_selector('.grid.grid-cols-12')
        if grid:
            t_el = await grid.query_selector('h1')
            if t_el: disc_title = (await t_el.inner_text()).strip()
            
            organized_section = await grid.query_selector('div[class*="2xl:col-span-3"]')
            if organized_section:
                p_el = await organized_section.query_selector('.flex.items-start.gap-2 p')
                if p_el: organized_by = (await p_el.inner_text()).strip()
            
            loc_elements = await grid.query_selector_all('.flex.items-center.gap-2.mb-2')
            if len(loc_elements) > 0:
                disc_location = (await loc_elements[0].inner_text()).strip()
                a_tag = await loc_elements[0].query_selector('a')
                if a_tag: location_href = await a_tag.get_attribute('href')
            
            web_a = await grid.query_selector('a.custom-visit-website')
            if web_a: website_link = await web_a.get_attribute('href')
            
            desc_el = await grid.query_selector('.prose.max-w-none.individual_page_description')
            if desc_el: description = (await desc_el.inner_text()).strip()
    except Exception as e:
        print(f"Error on detail page {full_link}: {e}")
    finally:
        await page.close() 
    return full_link, description, disc_title, disc_location, location_href, website_link, organized_by

async def fetch_coinpedia():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
        page = await context.new_page()
        url = "https://events.coinpedia.org/"
        try:
            print(f"Opening {url}...")
            await page.goto(url, wait_until="load", timeout=60000)
            await page.wait_for_selector('.event_card', timeout=20000)
            cards = await page.query_selector_all('.event_card')
            
            count = 0
            for card in cards[:20]: # 20 cards tak check kar lete hain
                data = {}
                first_div = await card.query_selector('.min-h-\\[150px\\]')
                if first_div:
                    img_tag = await first_div.query_selector('img')
                    data['image_src'] = await img_tag.get_attribute('src') if img_tag else "No Image"
                
                p_div = await card.query_selector('.relative.p-4')

                if p_div:
                    status_h6 = await p_div.query_selector('h6.text-sm.font-medium.flex.items-center.flex-wrap.gap-2')
                    if status_h6:
                        first_span = await status_h6.query_selector('span')
                        data['status'] = (await first_span.inner_text()).strip() if first_span else "N/A"
                    else:
                        data['status'] = "N/A"
                    p_a_tag = await p_div.query_selector('a')
                    if p_a_tag:
                        data['anchor_text'] = (await p_a_tag.inner_text()).strip()
                        raw_link = await p_a_tag.get_attribute('href')
                        
                        mt_div = await p_div.query_selector('.md\\:mt-\\[15px\\]')
                        if mt_div:
                            desc_div = await mt_div.query_selector('.text-sm.line-clamp-2')
                            data['location'] = (await desc_div.inner_text()).strip() if desc_div else "N/A"
                            
                            h5_div = await mt_div.query_selector('.flex.items-start.gap-4.mb-3')
                            if h5_div:
                                h5_tag = await h5_div.query_selector('h5')
                                data['date_text'] = (await h5_tag.inner_text()).strip() if h5_tag else "N/A"

                        if raw_link:
                            # Detail page par jane se pehle check nahi kar sakte kyunke description detail page se aani hai
                            f_url, f_desc, d_title, d_loc, loc_url, web_url, org_by = await get_full_description(context, raw_link)
                            
                            data.update({
                                'full_url': f_url, 'full_desc': f_desc, 'disc_title': d_title,
                                'disc_location': d_loc, 'location_href': loc_url,
                                'website_link': web_url, 'organized_by': org_by
                            })
                            
                            saved = await save_event(data)
                            if saved: count += 1
                            
            print(f"Process Finished! {count} new events added.")
        except Exception as e:
            print(f"Playwright Scraping Error: {e}")
        finally:
            await browser.close()

class Command(BaseCommand):
    help = 'Fetches events from Coinpedia and avoids duplicates'
    def handle(self, *args, **options):
        asyncio.run(fetch_coinpedia())