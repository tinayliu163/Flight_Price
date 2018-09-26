from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from unidecode import unidecode
import numpy as np
import pandas as pd
import requests
from bs4 import BeautifulSoup
import json

import time
from selenium.webdriver import ActionChains

headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_3) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/69.0.3497.100 Safari/537.36'}
base_url = "https://www.beyondmenu.com"

"""
get_res_data function :scrape restaurant name and address

- add sleep time in order to make next move until the web is fully loaded
- to test the code, please download Chrome WebDriver for mac or windows and 
  keep this notebook and chromedriver in the same folder or put the full path of chromedriver downlowned into the local

https://chromedriver.storage.googleapis.com/index.html?path=2.42/

param:

input_value: any city or zipcode, e.g.: "New York" or "07030"
return:

DataFrame: restaurant_address column and restaurant_name column

"""

def get_res_data(input_value):
    
    #created the instance of Chrome WebDriver, please download before creating
    driver = webdriver.Chrome("chromedriver") 
    #driver = webdriver.Chrome("/Users/yingliu/Documents/chromedriver") 
    driver.get(base_url) # navigate to this page
    time.sleep(2)
    city = driver.find_element_by_xpath('//*[@id="contentDesktop_HomeLandingCtrl_SearchInputCtrl_txtNewSearchAddress"]') 
    city.click()

   #send input_value to current focused element

    actions = ActionChains(driver)
    actions.send_keys(input_value)
    actions.send_keys(Keys.ENTER)
    actions.perform()

    time.sleep(1)
    
    driver.find_element_by_class_name('widebutton').click()
    
    # total pages
    total_pages = len(driver.find_element_by_id("contentDesktop_SearchResultCtrl1_restaurantListCtrl_lvSearchResults_ProductListPagerCombo").find_elements_by_tag_name("a"))
    page = 1
    all_name = [] # all restaurant name
    all_address = [] # all restaurant address

    while page <= total_pages:
        soup = BeautifulSoup(driver.page_source, "html.parser")
    # all restaurants in each page
        all_restaurant = soup.find_all("div",{"class" : "search_results"})
    
    # number of restaurants in each page
        num_restaurant = len(driver.find_element_by_class_name("search_results").find_elements_by_tag_name("a"))
    
        for i in range(0,num_restaurant):
            each_restaurant_link = all_restaurant[0].find_all('a',{'style':'display: block;'},href = True)[i]['href']
            response = requests.get(each_restaurant_link,headers = headers)
            each_restaurant_page = BeautifulSoup(response.content, "html.parser")
            
            # restaurant name
            name = each_restaurant_page.find_all('h1')[0].text
            all_name.append(name)
        
        # restaurant address
            address = each_restaurant_page.find_all('p',{"class": "cuisines"})[0].text.strip()
            address = address.split('\xa0')[0]
            all_address.append(address)
        
        if num_restaurant == 20:
            driver.find_element_by_link_text('Next').click()
            page = page +1
            time.sleep(2)
        else:
            break
    df = {'restaurant_name':all_name, 'restaurant_address': all_address}
    restaurant_data = pd.DataFrame(df)
    print(len(all_name))
    print(len(all_address))
    return restaurant_data.head()

## check with New York
result1 = get_res_data('New York')
print(result1)

# zipcode of Hoboken, NJ
result2 = get_res_data('07030')
print(result2)

