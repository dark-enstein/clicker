import requests
import yaml
import ssl
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
import os
from datetime import date

# functions

def load_os_env(path):
    file = open(path, "r")
    loaded = yaml.load(file, Loader=SafeLoader)
    secrets = {}
    secrets['RECEPIENTS'] = loaded['smtp']['recipients']
    secrets['FROM'] = loaded['smtp']['from']
    secrets['SMTP_SERVER'] = loaded['smtp']['server']
    secrets['USERNAME'] = loaded['smtp']['auth']['username']
    secrets['PASSWORD'] = loaded['smtp']['auth']['password']
    return secrets

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

def send_to_email(df, s):
    # send email containing df to recipient(s)
    
    emaillist = [elem.strip().split(',') for elem in s['RECEPIENTS']]
    msg = MIMEMultipart()
    msg['Subject'] = "Top Picks: " + str(date.today())
    msg['From'] = "ayobama72@gmail.com"


    html = """\
    <html>
      <head></head>
      <body>
        {0}
      </body>
    </html>
    """.format(df.to_html())

    part1 = MIMEText(html, 'html')
    msg.attach(part1)

    context = ssl.create_default_context()

    with smtplib.SMTP_SSL(s['SMTP_SERVER'], 465, context=context) as server:
        server.login(s['USERNAME'], s['PASSWORD'])
        server.sendmail(msg['From'], emaillist , msg.as_string())
        
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
SMTP_SERVER = ""

opportunities = {}
max_page_number = 1
total_found = []

s = load_os_env("./gama/config.yaml")

print("URLs loaded:", list(url.keys()))

for val in tqdm(url.values()):
    domain_pages(val)

# convert to python.dataframe
df = pd.DataFrame(opportunities.items(), columns=['Opportunity','URL'])
df['target_found'] = total_found

# send table as email
send_to_email(df, s)