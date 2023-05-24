from selenium import webdriver
import undetected_chromedriver.v2 as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait as wait
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
import pandas as pd
from pathlib import Path
import time
import os
import random
import shutil
import time
import unidecode
import calendar

def initialize_bot():

    # Setting up chrome driver for the bot
    chrome_options  = webdriver.ChromeOptions()
    # suppressing output messages from the driver
    chrome_options.add_argument('--log-level=3')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--disable-extensions')
    chrome_options.add_argument('--window-size=1920,1080')
    # adding user agents
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/87.0.4280.88 Safari/537.36")
    chrome_options.add_argument("--incognito")
    chrome_options.add_experimental_option('excludeSwitches', ['enable-logging'])
    # running the driver with no browser window
    chrome_options.add_argument('--headless')
    # installing the chrome driver
    driver_path = ChromeDriverManager().install()
    # configuring the driver
    driver = webdriver.Chrome(driver_path, options=chrome_options)
    driver.set_page_load_timeout(60)
    driver.maximize_window()

    return driver

def scrape_groupguides():

    months = list(calendar.month_name[1:])
    start = time.time()
    print('-'*75)
    print('Scraping groupguides.com ...')
    print('-'*75)
    # initialize the web driver
    driver = initialize_bot()

    # initializing the dataframe
    data = pd.DataFrame(columns=['Title', 'Title Link', 'Author', 'Author Link', 'Genre', 'Publisher', 'Release Date', 'Number Of Pages', 'Cover', 'ISBN-10', 'ISBN-13', 'Purchase Link'])
    driver.get('https://www.readinggroupguides.com/reviews/genres')
    time.sleep(3)
    links = []

    for _ in range(3):
        try:
            # getting the list of books genres
            genres = []
            genres_divs = wait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.views-row-unformatted")))
            nrows = len(genres_divs)
            for i, genre in enumerate(genres_divs):
                a = wait(genre, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                name = a.get_attribute("textContent")
                link = a.get_attribute("href")
                genres.append(link)

            # scraping books under each genre
            for j, link in enumerate(genres):
                print("-"*75)
                print(f'Scraping books urls under Genre {j+1}')
                driver.get(link)
                n = 0
                while True:
                    divs = wait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.title")))
                    for div in divs:
                        print(f"Getting the link for book {n+1}")
                        a = wait(div, 5).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        links.append(a.get_attribute("href"))
                        n += 1
                    # moving to the next page
                    try:
                        li = wait(driver, 2).until(EC.presence_of_element_located((By.CSS_SELECTOR, "li.pager-next")))
                        button = wait(li, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                        driver.execute_script("arguments[0].click();", button)
                    except:
                        break

            # scraping books details
            print('-'*75)
            print('Scraping Books Info...')
            print('-'*75)
            n = len(links)
            for i, link in enumerate(links):
                print(f'Scraping the info for book {i+1}\{n}')

                # title and title link
                title_link, title = '', ''
                try:
                    driver.get(link)
                    title_link = link
                    title = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//h2[@id='page-title']"))).text.title() 
                    title = unidecode.unidecode(title)
                except:
                    print(f'Warning: failed to scrape the title for book: {link}')            
                
                # author and author link
                author, author_link = '', ''
                try:
                    div = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='author']")))
                    a = wait(div, 2).until(EC.presence_of_element_located((By.TAG_NAME, "a")))
                    author = a.get_attribute("textContent")
                    author = unidecode.unidecode(author)
                    author_link = a.get_attribute("href")
                except:
                    pass            
            
                #purchase link
                book_link = ''
                try:
                    ul = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//ul[@id='buy-links']")))
                    urls = wait(ul, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "a")))
                    for url in urls:
                        book_link = url.get_attribute("href")
                        if 'amazon.com' in book_link: break
                except:
                    pass            
            
                #other info
                release_date, npages, publisher, ISBN10, ISBN13, genre, cover = '', '', '', '', '', '', ''
                try:
                    div = wait(driver, 2).until(EC.presence_of_element_located((By.XPATH, "//div[@id='book-data']")))
                    lis = wait(div, 2).until(EC.presence_of_all_elements_located((By.TAG_NAME, "li")))
                    for li in lis:
                        text = li.get_attribute("textContent")
                        tag = text.split(':')[0]
                        try:
                            if 'Publication Date' in tag:
                                release_date = text.split(':')[-1].strip()
                            elif 'Genres' in tag:
                                genre = text.split(':')[-1].strip()
                            elif 'Paperback' in tag or 'Hardcover'in tag:
                                npages = text.split(':')[-1].strip().split(' ')[0] 
                                cover = tag.strip()
                            elif 'Publisher' in tag:
                                publisher = text.split(':')[-1].strip()
                            elif 'ISBN-10' in tag:
                                ISBN10 = text.split(':')[-1].strip() 
                            elif 'ISBN-13' in tag:
                                ISBN13 = text.split(':')[-1].strip()
                        except:
                            pass
                except:
                    pass
            
                # appending the output to the datafame
                data = data.append([{'Title':title, 'Title Link':title_link, 'Author':author, 'Author Link':author_link, 'Genre':genre, 'Publisher':publisher, 'Release Date':release_date, 'Number Of Pages':npages, 'Cover':cover, 'ISBN-10':ISBN10, 'ISBN-13':ISBN13, 'Purchase Link':book_link}])
            break
        except:
            print('Error occurred during the scraping from CliffsNotes.com, retrying ..')
            driver.quit()
            time.sleep(5)
            driver = initialize_bot()

    # optional output to csv
    data.to_csv('groupguides_data.csv', encoding='UTF-8', index=False)
    elapsed = round((time.time() - start)/60, 2)
    print('-'*75)
    print(f'groupguides.com scraping process completed successfully! Elapsed time {elapsed} mins')
    print('-'*75)
    driver.quit()

    return data

if __name__ == "__main__":

    data = scrape_groupguides()

