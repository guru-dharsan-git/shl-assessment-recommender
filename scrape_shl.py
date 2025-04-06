import requests
from bs4 import BeautifulSoup
import csv
import re
import time

type_skill_map = {
    'A': 'Ability & Aptitude',
    'B': 'Biodata and Situational Judgement',
    'C': 'Competencies',
    'D': 'Development & 360',
    'E': 'Assessment Exercises',
    'K': 'Knowledge and Skills',
    'P': 'Personality and Behaviour',
    'S': 'Simulations',
}

urls = [
    'https://www.shl.com/solutions/products/product-catalog/?start=0&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=12&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=24&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=36&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=48&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=60&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=72&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=84&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=96&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=108&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=120&type=2&type=2',
    'https://www.shl.com/solutions/products/product-catalog/?start=132&type=2&type=2',
]

data = []

for url in urls:
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    rows = soup.find_all('tr', attrs={'data-course-id': True})

    for row in rows:
        title_cell = row.find('td', class_='custom__table-heading__title')
        a_tag = title_cell.find('a') if title_cell else None
        title = a_tag.get_text(strip=True) if a_tag else "N/A"
        link = a_tag['href'] if a_tag else "#"
        if not link.startswith("http"):
            link = "https://www.shl.com" + link

        remote_cell = row.find_all('td', class_='custom__table-heading__general')[0]
        remote_testing = "Yes" if remote_cell.find('span', class_='catalogue__circle -yes') else "No"

        adaptive_cell = row.find_all('td', class_='custom__table-heading__general')[1]
        adaptive_irt = "Yes" if adaptive_cell.find('span', class_='catalogue__circle -yes') else "No"

        type_cell = row.find('td', class_='product-catalogue__keys')
        type_spans = type_cell.find_all('span', class_='product-catalogue__key') if type_cell else []
        type_string = ''.join(span.get_text(strip=True).upper() for span in type_spans)

        skills = ', '.join([type_skill_map.get(char, '') for char in type_string if char in type_skill_map])

        try:
            product_response = requests.get(link)
            product_soup = BeautifulSoup(product_response.content, 'html.parser')
            description_div = product_soup.find('div', class_='product-catalogue-training-calendar__row typ')
            description = ""
            duration = ""

            if description_div:
                p_tag = description_div.find('p')
                if p_tag:
                    full_text = p_tag.get_text(strip=True)
                    description = full_text
                    match = re.search(r'Approximate Completion Time in minutes\s*=\s*(\d+)', full_text)
                    duration = match.group(1) if match else ""

        except Exception as e:
            description = "Error fetching description"
            duration = ""

        data.append([title, link, remote_testing, adaptive_irt, type_string, skills, description, duration])
        time.sleep(0.5)

csv_file = "shl_assessments_with_skills.csv"
with open(csv_file, mode='w', newline='', encoding='utf-8') as file:
    writer = csv.writer(file)
    writer.writerow([
        "Name", "URL", "RemoteTesting", "AdaptiveSupport", "Type", "Skills", "Description", "Duration"
    ])
    writer.writerows(data)

print(f"🎯 Data with skills saved to '{csv_file}'")
