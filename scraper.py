import os
import re
import requests
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor

BASE_URL = "https://papers.nips.cc"
SAVE_DIR = "downloads"
THREAD_COUNT = 5 
MAX_YEARS = 6 


def get_year_links():
    """Fetches the available paper years and sorts them in descending order."""
    response = requests.get(f"{BASE_URL}/paper_files/paper/")
    soup = BeautifulSoup(response.text, "html.parser")
    year_links = [BASE_URL + a["href"] for a in soup.select('a[href^="/paper_files/paper/"]')]
    return sorted(year_links, reverse=True)[:MAX_YEARS]  


def scrape_year(year_url):
    """Extracts all paper links for a given year."""
    response = requests.get(year_url)
    soup = BeautifulSoup(response.text, "html.parser")

    paper_links = []
    
    
    paper_links += [BASE_URL + a["href"] for a in soup.select('a[href$="-Abstract-Conference.html"]')]

   
    paper_links += [BASE_URL + a["href"] for a in soup.select('a[href*="/hash/"][href$="-Abstract.html"]')]

    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        for paper_url in paper_links:
            executor.submit(download_pdf, paper_url, year_url)


def download_pdf(paper_url, year_url):
    """Downloads a paper's PDF and saves it with the paper's title."""
    response = requests.get(paper_url)
    soup = BeautifulSoup(response.text, "html.parser")

    
    title_tag = soup.select_one("h4") or soup.select_one('a[title]')
    title = title_tag.text.strip() if title_tag else "Untitled"
    title = sanitize_filename(title)

   
    year = re.search(r"paper/(\d+)", year_url)
    year = year.group(1) if year else "Unknown"

   
    pdf_link = soup.select_one('a[href$=".pdf"]')
    if pdf_link:
        pdf_url = BASE_URL + pdf_link["href"]
        save_pdf(pdf_url, title, year)


def save_pdf(pdf_url, title, year):
    """Downloads and saves the PDF with a formatted filename."""
    year_dir = os.path.join(SAVE_DIR, year)
    os.makedirs(year_dir, exist_ok=True)

    file_path = os.path.join(year_dir, f"{title}.pdf")
    response = requests.get(pdf_url, stream=True)
    with open(file_path, "wb") as f:
        for chunk in response.iter_content(1024):
            f.write(chunk)

    print(f"Downloaded: {file_path}")


def sanitize_filename(name):
    """Removes invalid characters for filenames."""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


if __name__ == "__main__":
    year_links = get_year_links()
    
    with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
        for year_url in year_links:
            executor.submit(scrape_year, year_url)
