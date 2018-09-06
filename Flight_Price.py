#@author : Ying liu
# coding: utf-8
# Python 3
"""
Missions:
- scrape_date function: scrape Google flight price trend in the future 90 days after the start_date
- dbscan_outlier function: find outlier prices
- cheap_period function: find the cheapest period to fly

tip: need to download the latest chromedriver 

"""
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
import time
import datetime
from unidecode import unidecode
from sklearn.cluster import DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM
import numpy as np
import matplotlib.pyplot as plt
from dateutil.parser import parse
import pandas as pd
import random
import matplotlib
import warnings
import math
from scipy.spatial import distance

warnings.filterwarnings('ignore')
matplotlib.style.use('ggplot')
# %matplotlib inline

import time
from selenium.webdriver import ActionChains

# add wait method to ActionChains class
# http://stackoverflow.com/questions/36572190/specify-wait-time-between-actions-when-using-selenium-actionchains
class ActionChains(ActionChains):
    def wait(self, time_s):
        self._actions.append(lambda: time.sleep(time_s))
        return self

"""
scrape_data function :scrape Google flight price trend in the future 90 days

trick: add sleep time in order to make next move until the web is fully loaded

param:
- start_date: datetime object for the start date used in the query to Google Flight explorer. e.g. '2018-08-07'
- return_date: datetime object for the return data
- from_place: string for the name of the departure of the flights. e.g. 'New York City'
- to_place: string for the name of the regional destination of the flights. e.g. 'London'

return:
- DataFrame: Date_of_Fight column and Price column


"""

def scrape_data(start_date,return_date,from_place, to_place):
    base_url = "https://www.google.com/flights/explore/"
    # created the instance of Chrome WebDriver
    driver = webdriver.Chrome("chromedriver") 
    driver.get(base_url) # navigate to this page
    time.sleep(4)
    
    # input from_place
    # locate the element by xpath
    from_input = driver.find_element_by_xpath('//*[@id="flt-app"]/div[2]/main[1]/div[4]/div[1]/div[2]/div[2]/div[1]/div[3]/span[2]/span/span[2]') 
    from_input.click()
    # send keys to current focused element
    ActionChains(driver).wait(1).send_keys(from_place).perform()  
    ActionChains(driver).wait(1).send_keys(Keys.ENTER).perform()
    
    time.sleep(4)
    # input to_place    
    to_input = driver.find_element_by_class_name('gws-flights-form__text-field-placeholder')
    to_input.click()
    
    time.sleep(4)
    ActionChains(driver).wait(1).send_keys(to_place).perform()
    ActionChains(driver).wait(1).send_keys(Keys.ENTER).perform()
    
    time.sleep(4)
    
    ## click search button
    driver.find_element_by_xpath('//*[@id="flt-app"]/div[2]/main[1]/div[4]/div[1]/div[2]/div[4]/floating-action-button').click()
    
    # define a price list
    # define a date list
    prices = []
    dates = []
    
    for i in range(0,90):
        current_link = driver.current_url
        # start_date
        departure_date = start_date + datetime.timedelta(days=i)
        start_date_str = departure_date.strftime("%Y-%m-%d")
        # return_date
        leave_date = return_date + datetime.timedelta(days=i)
        return_date_str = leave_date.strftime("%Y-%m-%d")
        
        list_of_string = current_link.split('*') #split current url by '*'
        # create url
        url = list_of_string[0][:-10] + start_date_str + '*' + list_of_string[1][:-29] + return_date_str + list_of_string[1][-19:]
        driver.get(url)
        
        # price graph
        price_trend = driver.find_element_by_xpath('//*[@id="flt-app"]/div[2]/main[2]/div[9]/div[1]/div[2]/div[2]/div/div[3]/div/div[6]/div/div[2]/div[2]')
        driver.execute_script("arguments[0].click();", price_trend)
        time.sleep(6)
    
        #price
        price = driver.find_element_by_xpath('//*[@id="flt-flight-insights"]/div[2]/div[2]/div/div[2]/price-graph/div[1]/div[1]/div[2]/div[6]/span').text
        time.sleep(5)
        
        # date
        date = driver.find_element_by_xpath('//*[@id="flt-flight-insights"]/div[2]/div[2]/div/div[2]/price-graph/div[1]/div[1]/div[1]/jsl[2]/jsl[2]/jsl[1]').text
        # check
        #print(date)
        time.sleep(5)
        prices.append(price)
        dates.append(date)
        
        time.sleep(4)
      
    prices_new = [int(d.replace('$', '')) for d in prices]
    df = pd.DataFrame({'Date_of_Flight':dates,'Price':prices_new})
    return df

"""
dbscan_outlier function
- objective: Find outlier prices (specifically those which are less than what is considered a "normal" price)
- find noise points
- calculate Euclidean distance

param:
- DataFrame object returned from scrape_data function

return:
- DataFrame object with Outlier Prices

"""                              


def dbscan_outlier(data):
    # e.g.: convert Aug 21 to 2018-08-21
    data['Date_of_Flight'] = [parse(date) for date in list(data['Date_of_Flight'].values)]
    # Day : 1,2,3,4,...,90
    data['Day'] = (data['Date_of_Flight'] - data['Date_of_Flight'][0]).dt.days + 1
    day = np.array(data['Day'],dtype = pd.Series)
    price = np.array(data['Price'],dtype = pd.Series)
    array = np.concatenate([day[:, None], price[:, None]], axis=1) 
    X = StandardScaler().fit_transform(data[['Day', 'Price']])
    
    # run dbscan
    # find clusters
    db = DBSCAN(eps= .3, min_samples=6).fit(X)  
     
    labels = db.labels_
    data['label'] = labels
    
    #number of cluster
    n_clusters = len(set(labels)) 
    unique_labels = set(labels)
    colors = plt.cm.Spectral(np.linspace(0, 1, len(unique_labels)))
    plt.subplots(figsize=(12,8))
    
    for k, c in zip(unique_labels, colors):
        class_member_mask = (labels == k) # Boolean
        xy = X[class_member_mask] # price and date data for that specific label
        plt.plot(xy[:, 0], xy[:, 1], 'o', markerfacecolor=c,
                 markeredgecolor='k', markersize=14)
    plt.title("Total Clusters: {}".format(n_clusters), fontsize=14,y=1.01)
    
    # save image
    plt.savefig('dbscan_cluster.png')

    outlier_price_index = []

    # find noise points
    noise_points = data[data['label'] == -1]

    lbls = np.unique(db.labels_)

    # calculate the cluster mean vertically across row   
    # list of array(day_mean,price_mean) for each cluster

    cluster_means = [np.mean(array[labels==num, :], axis=0) for num in lbls if num != -1] 

    for index in noise_points.index:
        min_cluster_index = 0
        min_dist = 10000
        # noise_price
        outlier_x = data.loc[index].Day
        outlier_y = data.loc[index].Price
        for i, (cluster_mean_x, cluster_mean_y) in enumerate(cluster_means): # i: index of cluster
        
            # Euclidean distance: from each noise point to each cluster
            dist = distance.euclidean(np.array([outlier_x, outlier_y]), np.array([cluster_mean_x, cluster_mean_y]))
            if dist < min_dist:
                min_dist = dist
                min_cluster_index = i
        # closest cluster for each noise point
        # the Euclidean distance from that noise point to its closest cluster will be minimum
        closest_cluster = data[data['label'] == min_cluster_index]
        std = np.std(closest_cluster.Price)
        mean = np.mean(closest_cluster.Price)
        
        # threshold 
        thrhd = max(mean - 2 * std, 50)
        
        if data.loc[index].Price < thrhd:
            outlier_price_index.append(index) 
            
    if outlier_price_index :
        return data.loc[outlier_price_index]
    else:
        print ('no outlier prices found')

"""
cheap_period function: find the cheapest "period" to fly.
- define a period as a contiguous set of 5 days where the overall price doesn't fluctuate more than $20 between any 2 days.
- the function is to find the best period not the best single price. 
In other words, that best price you will buy might not be included in the period give by this function

param:
- DataFrame object returned from scrape_data function

return:
- Dataframe with 5 rows. The cheapest period

"""
def cheap_period(df):
        
    #the difference between prices within continuous two days should be no more than 20
    start_date = df.Date_of_Flight[0]
    day = np.array(df['Day'],dtype = pd.Series)
    day = day * 30 # do the scaling 
    price = np.array(df['Price'],dtype = pd.Series)
    X = np.concatenate([day[:, None], price[:, None]], axis=1) 
    
    # a = 30 (represent the difference between continuous two days)
    # b = 20 (the difference between prices within continuous two days should be no more than 20)
    # sqrt(a^2 + b^2) = 36.055
    # if the distance from (30,21) [this point should not be included] to original point should be euclidean distance
    # euclidean distance: 36.61966684720111
    # epsilon can be [36.055,36.61966684720111]
  
    db = DBSCAN(eps=36.4, min_samples=3).fit(X)
    df['label'] = db.labels_

    unique_labels = set(db.labels_)
    #print(unique_labels)
    
    # lists of all possible cheap periods
    list_of_dfs = []
    # cluster label -1 is the noise data, only consider other labels
    for label in unique_labels:
        if label != -1:
            one_cluster = df[df['label'] == label]
            
            # find start/end date for every 5-day-consecutive period
            consecutive_list = []
            days = one_cluster['Day'].values
            for i in range(len(days) - 4):
                if days[i + 4] - days[i] == 4: # 5 continuous days
                    consecutive_list.append((days[i], days[i + 4])) # e.g.: (60,64)

            # a list of 5-day-consecutive period dataframes
            for start, end in consecutive_list:
                df_five_day = one_cluster.loc[start - 1:end - 1, ['Day', 'Price']]
                               
                # criteria : the difference between minimum price and the maximum price <= $20.
                if df_five_day['Price'].describe()['max'] - df_five_day.Price.describe()['min'] <= 20:
                        df_five_day.Day = df_five_day.Day.apply(
                        lambda x: (start_date + datetime.timedelta(
                            days=x - 1)).strftime('%Y-%m-%d'))
                    
                        list_of_dfs.append(df_five_day)
                               
    # of all possible cheap periods, return a continuous 5 day period with the lowest average price.                         
    means = [one_df.Price.mean() for one_df in list_of_dfs]
    df_min_index = means.index(min(means))
    print(" The lowest average price: {}".format(min(means)))
    return list_of_dfs[df_min_index]

## Test

print("************************ function 1 ********************************")
flight_data = scrape_data(parse('2018-08-10'), parse('2018-08-13'),'New York City','London')
#print(flight_data)

print("************************ function 2 ********************************")
outlier_price = dbscan_outlier(flight_data)
#print(outlier_price)

print("************************ function 3 ********************************")
cheapest_period = cheap_period(flight_data)
#print(cheapest_period)






            



