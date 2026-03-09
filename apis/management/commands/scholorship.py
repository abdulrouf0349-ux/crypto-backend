# import requests
# from bs4 import BeautifulSoup


# def href_list(hrefs):
#     """Extracts paragraphs from the detail page."""
#     try:
#         response = requests.get(hrefs, headers=headers)
#         soup = BeautifulSoup(response.text, "html.parser")

#         se_div = soup.select_one('div.entry.clearfix')  # ✅ Corrected here

#         if not se_div:
#             return ["No Description Section Found"]

#         paragraphs = se_div.find_all('p')[4:]
#         data = []

#         for p in paragraphs:
#             text = p.text.strip()
#             if text:
#                 data.append(text)

#         return data if data else ["No Description Found"]

#     except Exception as e:
#         print(f"Error retrieving description for {hrefs}: {e}")
#         return ["Error Retrieving Description"]

# url = "https://www.scholars4dev.com/tag/scholarships-for-pakistans/"
# headers = { "User-Agent": "Mozilla/5.0" }

# response = requests.get(url, headers=headers)
# soup = BeautifulSoup(response.text, "html.parser")

# # Get the main content section
# first_div = soup.find('div', id='content')
# sec_div = first_div.select('div.post.clearfix')[:10]  # ✅ Exact match, no nested duplicates

# print(f"✅ Total unique posts found: {len(sec_div)}")

# for d in sec_div:
#     h2_tag = d.find('h2')
#     title = h2_tag.text.strip() if h2_tag else "No Title Found"  #Title
#     next_temp_link = h2_tag.find('a')['href'] if h2_tag and h2_tag.find('a') else "No Link Found"  #next Link
#     div_for= d.find_all('div', class_='post_column_1')

#     # for data in div_for:
#     requirment = div_for[0].find('p').text.strip() if div_for and div_for[0].find('p') else "No Education Found" #education
#     # print("🔹 Title:", education)

#     deadline = div_for[1].find('p').text.strip() if div_for and div_for[1].find('p') else "No Education Found" #deadline
#     # print("🔹 Title:", deadline)


#     update_datee=d.select_one('div.postdate.clearfix')
#     expire_or_not = update_datee.find('div',class_='left').text.strip() if update_datee and update_datee.find('div', class_='left') else "No Update Date Found"  #update date
#     # print("🔹 Update Date:", update_date)
    
#     discription = href_list(next_temp)  #description
#     print("🔹 Description:", discription)



import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from apis.models import ScholorshipJob
from django.utils.text import slugify


class Command(BaseCommand):
    help = 'Scrapes scholarship data and saves to DB'

    def handle(self, *args, **kwargs):
        url = "https://www.scholars4dev.com/tag/scholarships-for-pakistans/"
        headers = { "User-Agent": "Mozilla/5.0" }

        try:
            response = requests.get(url, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            first_div = soup.find('div', id='content')
            sec_div = first_div.select('div.post.clearfix')[:10]  # Limit to first 10 posts

            print(f"✅ Total posts found: {len(sec_div)}")

            for d in sec_div:
                h2_tag = d.find('h2')
                title = h2_tag.text.strip() if h2_tag else "No Title Found"
                link = h2_tag.find('a')['href'] if h2_tag and h2_tag.find('a') else None

                if not link or ScholorshipJob.objects.filter(link=link).exists():
                    print(f"⏩ Skipping duplicate or invalid entry: {title}")
                    continue  # Skip duplicates

                div_for = d.find_all('div', class_='post_column_1')

                requirment = div_for[0].find('p').text.strip() if div_for and div_for[0].find('p') else "No Requirement Found"
                deadline = div_for[1].find('p').text.strip() if len(div_for) > 1 and div_for[1].find('p') else "No Deadline Found"

                update_datee = d.select_one('div.postdate.clearfix')
                expire_or_not = update_datee.find('div', class_='left').text.strip() if update_datee and update_datee.find('div', class_='left') else "No Update Date Found"

                description = self.get_description(link)
                description_text = "\n".join(description)

                # Save to DB
                ScholorshipJob.objects.create(
                    title=title,
                    slug=slugify(title),
                    link=link,
                    requirment=requirment,
                    deadline=deadline,
                    expire_date_not=expire_or_not,
                    discription=description_text
                )

                print(f"✅ Saved: {title}")

        except Exception as e:
            print(f"❌ Error in scraping: {e}")

    def get_description(self, href):
        try:
            headers = { "User-Agent": "Mozilla/5.0" }
            response = requests.get(href, headers=headers)
            soup = BeautifulSoup(response.text, "html.parser")
            se_div = soup.select_one('div.entry.clearfix')

            if not se_div:
                return ["No Description Section Found"]

            paragraphs = se_div.find_all('p')[4:]  # Skip first 4
            data = [p.text.strip() for p in paragraphs if p.text.strip()]
            return data if data else ["No Description Found"]

        except Exception as e:
            print(f"❌ Error retrieving description for {href}: {e}")
            return ["Error Retrieving Description"]
