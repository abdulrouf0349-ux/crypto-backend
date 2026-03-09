def jobs_link(hrefs):
    """Extracts hrefs and images from the job listing page."""
    try:
        response = requests.get(hrefs, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        url_for_job=soup.find('td',class_='job-information')
        for_job_link = url_for_job.find('a')['href'] if url_for_job and url_for_job.find('a') else "No Job Link Found"
        return for_job_link
    except Exception as e:
        print(f"Error retrieving image for {hrefs}: {e}")
        return "Error Retrieving Image"
    
def href_list(hrefs):
    """Extracts hrefs and images from the job listing page."""
    try:
        response = requests.get(hrefs, headers=headers)
        soup = BeautifulSoup(response.text, "html.parser")
        
        img = soup.find('div', class_='job-ad-container')
        img_url = img.find('img')['src'] if img and img.find('img') else "No Image Found"
        url_for_job=soup.find('td',class_='job-information')
        for_job_link = url_for_job.find('a')['href'] if url_for_job and url_for_job.find('a') else "No Job Link Found"

        return f"https://www.pakistanjobsbank.com{img_url}" if img_url != "No Image Found" else img_url,for_job_link
    except Exception as e:
        print(f"Error retrieving image for {hrefs}: {e}")
        return "Error Retrieving Image"
import requests
from bs4 import BeautifulSoup

URL = "https://www.pakistanjobsbank.com/"
headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)
soup = BeautifulSoup(response.text, "html.parser")

# Get the main table containing job listings
table = soup.find("table")
# Find all job listing rows
rows = table.find_all("tr", class_="job-ad")

data_list = []

# Loop through each job listing row
for index, row in enumerate(rows, start=1):
    title_tag = row.find("td")  # Get the first <td> for the job listing info
    job_title = row.find_all("td")[1]  # Get the second <td> for the job title
    
    if title_tag:
        time = title_tag.find('div').text.strip() if title_tag.find('div') else "No Time Found"
        
        # Get job title and link
        title = title_tag.find('a')
        titles = title.text.strip() if title else "No Title Found"

        href1 = title['href'] if title else "No Link Found"
        href2=f"https://www.pakistanjobsbank.com/{href1}"  # Ensure the link is absolute
        # Call href_list to get the image
        img_url = href_list(href2)
        img_urls,for_job_link = img_url
        
        # Extract job position info
        job_title1 = job_title.find('ul', class_='Positions').text.strip() if job_title.find('ul', class_='Positions') else "No Job Title Found"
        
        # Append data to the list
        print(for_job_link)
#         data_list.append([time, titles, href2, img_url, job_title1])
       

# # Print the final data list
# print("Job Listings:")
# for data in data_list:
#     print(f"Time: {data[0]} | Title: {data[1]} | Link: {data[2]} | Image URL: {data[3]} | Position: {data[4]}")