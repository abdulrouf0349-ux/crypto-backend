import requests
from bs4 import BeautifulSoup
from django.core.management.base import BaseCommand
from apis.models import jobz_pk
from django.utils.text import slugify

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
}

def get_details(job_links):
    """Extracts job image link from the job link page."""
    try:
        response = requests.get(job_links, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        description_div = soup.find('div', id='ad-pic-cont')
        description = description_div.find('a') if description_div else None
        img = description['href'] if description else "No Description Found"
        return img
    except Exception as e:
        print(f"Error retrieving details for {job_links}: {e}")
        return "Error Retrieving Details"

class Command(BaseCommand):
    help = "Scrape Jobz.pk overseas jobs and save to DB (skip duplicates)"

    def handle(self, *args, **kwargs):
        url = "https://www.jobz.pk/overseas-uae-dubai-uk-jobs/"
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        job_cards = soup.find("div", class_="first_big_4col")
        alldata = job_cards.find_all("div", class_="row_container")

        for data in alldata[1:]:  # skip first
            jobs_title = data.find("div", class_="cell1")
            if jobs_title:
                jobs_link = jobs_title.find("a")
                job_links = jobs_link['href'] if jobs_link else "No Link Found"
                job_title = jobs_link.text.strip() if jobs_link else "No Title Found"

                # 🔁 Check for duplicate using web_link
              

                image = get_details(job_links)
                if jobz_pk.objects.filter(image=image).exists():
                    print(f"Duplicate found, skipping: {job_title}")
                    self.stdout.write(self.style.SUCCESS(f"Saved: {job_title}"))
 
                    continue

                company_name = data.find("div", class_="cell2")
                company_link = company_name.find("a") if company_name else None
                company_links = company_link['href'] if company_link else "No Link Found"
                company_title = company_link.text.strip() if company_link else "No Title Found"

                city_name = data.find("div", class_="cell_three")
                city_li = city_name.find("div", class_="inner_cell") if city_name else None
                city_link = city_li.find("a") if city_li else None
                city_links = city_link['href'] if city_link else "No Link Found"
                city_title = city_link.text.strip() if city_link else "No Title Found"

                date_job = city_name.find_all("div", class_="inner_cell")[1] if city_name else None
                date_job_title = date_job.text.strip().split('\n')[0] if date_job else "No Date Found"

                # ✅ Save to DB
                jobz_pk.objects.create(
                    title=job_title,
                    slug=slugify(job_title),
                    web_link=job_links,
                    image=image,
                    company_title=company_title,
                    company_link=company_links,
                    city_title=city_title,
                    city_link=city_links,
                    date_job=date_job_title
                )
                print(f"Saved: {job_title}")
                self.stdout.write(self.style.SUCCESS(f"Saved: {job_title}"))

