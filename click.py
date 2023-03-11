import requests
import yaml
from yaml.loader import SafeLoader
from bs4 import BeautifulSoup
from tqdm import tqdm
from time import sleep
import pandas as pd
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.multipart import MIMEMultipart
from smtplib import SMTP
import smtplib
import sys

def load_os_env(path):
    file = open(path, "r")
    loaded = yaml.load(file, Loader=SafeLoader)
    USERNAME = loaded['smtp']['auth']['username']
    PASSWORD = loaded['smtp']['auth']['password']
    RECEPIENTS = loaded['smtp']['recipients']
    FROM = loaded['smtp']['from']

def domain_pages(url):
    # generate a dict of the title mapped to urls of opportunities for the cartegory url passed in 
    
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    
    pages = soup.find_all("div", {"class": "page-nav td-pb-padding-side"})
    page_array = [int(pages[0].find("span", {"class": "current"}).text), int(pages[0].find_all('a')[2].get('title'))]
    
    
    if page_array[1] > max_page_number:
        for page in range(page_array[0], max_page_number + 1):
            get_opportunities(url, page)
    else:
        for page in range(page_array[0], page_array[1]):
            get_opportunities(url, page)
            
    return

def get_opportunities(url, page):
    # parse the list of opportunities from the provided page
    curated_url = url+"page/"+str(page)+"/"
    page = requests.get(url+"page"+str(page))
    soup = BeautifulSoup(page.content, "html.parser")
    
    return parse_opportunities(soup)

def parse_opportunities(soup):
    # parse the list opportunities from the provided BeautifulSoup Object
    results = soup.find_all("h3", class_="entry-title td-module-title")

    for result in tqdm(results):
        opportunities[result.find('a').get('title')] = result.find('a').get('href')
        total_found.append(investigate_url_content(result.find('a').get('href')))
              
    return

def investigate_url_content(url):
    # search for target_search_list occurence in the url
    # if string(s) occur, append it to the df
    text = ""
    page = requests.get(url)
    soup = BeautifulSoup(page.content, "html.parser")
    result = soup.find_all("div", {"class": "td-post-content tagdiv-type"})[0].find_all(['p', 'ul', 'ol', 'h2'])
    for txt in result:
        text = text + txt.text
    
    found = ""

    for target in target_search_list:
        if target in text:
            found = found + " | " + target
        else:
            continue
    return found

def send_to_email(df, email):
    # send email containing df to recipient(s)
    return

# url setup
url = {}

# url['base_url'] = "https://www.opportunitiesforafricans.com/"
url['fellowships_url'] = "https://www.opportunitiesforafricans.com/category/fellowships/"
# url['internship_url'] = "https://www.opportunitiesforafricans.com/category/internships/"
# url['scholarships_masters_url'] = "https://www.opportunitiesforafricans.com/category/scholarships/"
# url['scholarships_postgraduate_url'] = "https://www.opportunitiesforafricans.com/category/scholarships/post-graduate/"
# url['scholarships_undergraduate_url'] = "https://www.opportunitiesforafricans.com/category/scholarships/undergraduate/"

"""
Supported URLs for Opportunity for Africans

base_url = "https://www.opportunitiesforafricans.com/" #doesn't have page number, may not be very needed
fellowships_url = "https://www.opportunitiesforafricans.com/category/fellowships/"
internship_url = "https://www.opportunitiesforafricans.com/category/internships/"
scholarships_masters_url = "https://www.opportunitiesforafricans.com/category/scholarships/"
scholarships_postgraduate_url = "https://www.opportunitiesforafricans.com/category/scholarships/post-graduate/"
scholarships_undergraduate_url = "https://www.opportunitiesforafricans.com/category/scholarships/undergraduate/"
call_for_nominations_url = "https://www.opportunitiesforafricans.com/category/calls-for-nomination/" (not supported)
call_for_papers_url = "https://www.opportunitiesforafricans.com/category/calls-for-papers/"
call_for_proposals_url = "https://www.opportunitiesforafricans.com/category/call-for-proposals/"
awards_url = "https://www.opportunitiesforafricans.com/category/awards/"

How to filter target searches?
Search for terms or expressions?
Doctoral := PhD
Nigerian specific: 
All persons: 
STEM words:
Cloud Engineering:
Matrials Engineering: 
Generics: "application", "candidates"
"""
target_search_list = ["application", "candidates"]

USERNAME = ""
PASSWORD = ""
RECEPIENTS = []
FROM = ""
opportunities = {}
max_page_number = 1
total_found = []

load_os_env("./gama/config.yaml")

print("URLs loaded:", list(url.keys()))

for val in tqdm(url.values()):
    domain_pages(val)

# convert to python.dataframe
df = pd.DataFrame(opportunities.items(), columns=['Opportunity','URL'])
df['target_found'] = total_found

# spit into csv, and email to me
df.to_csv('first_generation.csv')

# send table as email
# send_to_email(df, email)