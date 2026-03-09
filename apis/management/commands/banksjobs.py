


# your_app/management/commands/scrape_jobs.py

from django.core.management.base import BaseCommand
import requests
from bs4 import BeautifulSoup
from apis.models import JobBank  # Import your JobBank model

headers = {
    "User-Agent": "Mozilla/5.0"
}

def href_list(hrefs):
    """Extracts hrefs and images from the job listing page and saves to DB."""
    try:
        response = requests.get(hrefs, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Extract image URL
        img = soup.find('div', class_='job-ad-container')
        img_url = img.find('img')['src'] if img and img.find('img') else "No Image Found"
        url_for_job=soup.find('td',class_='job-information')
        for_job_link = url_for_job.find('a')['href'] if url_for_job and url_for_job.find('a') else "No Job Link Found"
        img_url = f"https://www.pakistanjobsbank.com{img_url}" if img_url != "No Image Found" else img_url,for_job_link
        
        # Return the image URL
        return img_url
    except Exception as e:
        print(f"Error retrieving image for {hrefs}: {e}")
        return "Error Retrieving Image"


class Command(BaseCommand):
    help = 'Scrape job listings and save them to the database'

    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting job listings scraping...'))

        URL = "https://www.pakistanjobsbank.com/"

        # Send request to the job listing page
        response = requests.get(URL, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")

        # Get the main table containing job listings
        table = soup.find("table")
        rows = table.find_all("tr", class_="job-ad")

        # Loop through each job listing row
        for index, row in enumerate(rows, start=1):
            title_tag = row.find("td")
            job_title = row.find_all("td")[1]  # Extract the second <td> for job title
            
            if title_tag:
                time = title_tag.find('div').text.strip() if title_tag.find('div') else "No Time Found"
                
                # Extract job title and link
                title = title_tag.find('a')
                titles = title.text.strip() if title else "No Title Found"
                divs = title_tag.find_all('div')
                raw_location = divs[-1].text.strip() if len(divs) >= 2 else "No Location Found"
                location = raw_location.replace("in ", "").strip()
                
                href1 = title['href'] if title else "No Link Found"
                href2 = f"https://www.pakistanjobsbank.com/{href1}"  # Make the link absolute
                if JobBank.objects.filter(job_title=titles).exists():
                 self.stdout.write(self.style.WARNING(f"Duplicate skipped: {titles}"))
                 continue
                
                # Call href_list function to get the image URL
                img_url = href_list(href2)
                img_urls,for_job_link = img_url
                
                # Extract job position info
                job_title1 = job_title.find('ul', class_='Positions')
                job_positions = job_title1.find_all('li') if job_title1 else []
                
                # Create a new JobBank entry in the database
              
                # Save each position as a related entry to the JobBank model
                job_positionss1 = []
                for position in job_positions:
                    job_positionss = position.text.strip() if position else "No Position Found"
                    job_positionss1.append(job_positionss)
                 
                job_listing = JobBank.objects.create(
                    job_title=titles,
                    Link=href2,
                    Image=img_urls,
                    Job_apply_link=for_job_link,
                    Time=time,
                    location=location,
                )
                job_listing.save_positions(job_positionss1)
                
                self.stdout.write(self.style.SUCCESS(f"Saved: {titles} | {time} | {href2} | {img_urls}"))

        self.stdout.write(self.style.SUCCESS('Job data scraping and saving completed!'))
