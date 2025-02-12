# %% [markdown]
# # Airbnb Rio de Janeiro listings data 
# All data was downloaded from [insideairbnb](https://insideairbnb.com/get-the-data/)


# #### Loading modules
import pandas as pd
import sqlalchemy
import os
import gzip
from dotenv import load_dotenv
import requests

# %% [markdown]

#  Load dotenv and create database engine
load_dotenv()
engine = sqlalchemy.create_engine('postgresql+psycopg2://postgres:secure-password@127.0.0.1:5432/pandas-study-db')

# %% [markdown]

# ## Bronze layer
# %% [markdown]

#  Extractin files from airbnb insider and loading with pandas

files = {
    'calendar': 'https://data.insideairbnb.com/brazil/rj/rio-de-janeiro/2024-12-27/data/calendar.csv.gz',
    'listings': 'https://data.insideairbnb.com/brazil/rj/rio-de-janeiro/2024-12-27/data/listings.csv.gz',
    'reviews': 'https://data.insideairbnb.com/brazil/rj/rio-de-janeiro/2024-12-27/data/reviews.csv.gz'
}

def download_and_extract(filename, url):
    gzb_path = f'data/{filename}.csv.gz'
    
    print(f'Downloading {filename} files...')
    response = requests.get(url, stream=True)
    with open(gzb_path, 'wb') as file:
        for chunk in response.iter_content(chunk_size=1024):
            file.write(chunk)
            
    print(f'Converting {filename} data into dataframes')
    with gzip.open(gzb_path, 'rt', encoding='utf-8') as file:
        df = pd.read_csv(file)
        
    os.remove(gzb_path)
    
    print(f'{filename} data loaded succesfully\n')
    
    return df

dataframes = {}

for filename, url in files.items():
    dataframes[filename] = download_and_extract(filename, url)

#%%

df_listings = dataframes['listings']
df_reviews = dataframes['reviews']
df_calendar= dataframes['calendar']


#%% [markdown]

# Listings preview:
df_listings.head()
#%% [markdown]

# Reviews preview:
df_reviews.head()
#%% [markdown]

# Calendar preview:
df_calendar.head()


# %% [markdown]

#  Saving the data from csv files on database
df_listings.to_sql('tb_bronze_listings', engine, if_exists='replace', index='False')
df_reviews.to_sql('tb_bronze_reviews', engine, if_exists='replace', index='False')
df_calendar.to_sql('tb_bronze_calendar', engine, if_exists='replace', index='False', chunksize=100000)


# %% [markdown]

# ## Silver layer
# %% [markdown]

# ### Listings

#  Checking inconsistent data values from `df_listings`
with pd.option_context('display.max_rows', None, 'display.max_columns', None):
    print(df_listings.isna().sum())

# %% [markdown]

#  Dropping inconsistent values from `df_listings`
df_listings = (df_listings.dropna(axis=1)
                            .reset_index())
df_listings.isna().sum()

# %% [markdown]

#  Dropping not used columns from `df_listings`
df_listings = (df_listings.drop(columns=['scrape_id', 'last_scraped', 'source', 'picture_url', 
                                        'latitude', 'longitude', 'amenities', 'minimum_nights', 
                                        'maximum_nights', 'minimum_minimum_nights', 'maximum_minimum_nights',
                                        'minimum_maximum_nights', 'maximum_maximum_nights', 'calendar_last_scraped',
                                        'index', 'listing_url', 'host_url', 'number_of_reviews_ltm', 'number_of_reviews_l30d'
                                        ])
                                        .rename(columns={'neighbourhood_cleansed': 'neighbourhood'})
                                        )
df_listings
# %% [markdown]

#  Transforming inconsistent values of `instant_bookable` column into valueable information from listings dataframe
df_listings['instant_bookable'] = df_listings['instant_bookable'].replace({'f': 'No', 't': 'Yes'})
df_listings['instant_bookable']

# %% [markdown]

# ### Reviews
# %% [markdown]
#  Checking inconsistent data values from `df_reviews`
df_reviews.isna().sum()

# %% [markdown]

#  Dropping inconsistent values from `df_reviews`
df_reviews = (df_reviews.dropna()
                        .reset_index(drop=True)
                        )
df_reviews.isna().sum()
# %% [markdown]

# ### Calendar

#  Executing data pipeline from `df_calendar`
df_calendar = (df_calendar.sort_values(['date'], ascending=False)
                            .drop(columns=['adjusted_price'])
                            .drop_duplicates(['listing_id'], keep='last')
                            .dropna()
                            .rename(columns={'date': 'last_listing_price_date', 'price': 'price_USD'})
                            .reset_index(drop=True))
df_calendar['last_listing_price_date'] = pd.to_datetime(df_calendar['last_listing_price_date'], format='%Y-%m-%d')
df_calendar
# %% [markdown]

#  Standardizing values from price column on Calendar dataframe
df_calendar['price_USD'] = df_calendar['price_USD'].str.replace(r'[$,]', '', regex=True)
df_calendar['price_USD'] = df_calendar['price_USD'].astype(float)
df_calendar['price_USD']

# %% [markdown]

#  Filtering price below zero and copying into `df_calendar`
price_condition = df_calendar['price_USD'] > 0
df_calendar = df_calendar[price_condition].copy()

# %% [markdown]

#  Requesting USD conversion rate to BRL from [ExchangeRate](https://www.exchangerate-api.com/)
api_key = os.getenv('EXCHANGE_API_KEY')
url = f'https://v6.exchangerate-api.com/v6/{api_key}/pair/USD/BRL'
response = requests.get(url)
data = response.json()
conversion_rate = data['conversion_rate']

# %% [markdown]

# Creating a new table to store BRL price

df_calendar['price_BRL'] = (df_calendar['price_USD'] * conversion_rate).round(decimals=2)
df_calendar['price_BRL']

# %% [markdown]

#  Transforming inconsistent values of `available` column into valueable information from Calendar dataframe
df_calendar['available'] = df_calendar['available'].replace({'f': 'No', 't': 'Yes'})
df_calendar['available']

# %% [markdown]

#  Sorting `df_calendar` before merge with `df_listings`
sorted_df_calendar = df_calendar[['listing_id', 'last_listing_price_date', 'price_USD', 'price_BRL', 'available', 'minimum_nights', 'maximum_nights']]
sorted_df_calendar

# %% [markdown]

#  Merging `df_listings` with `df_calendar`
df_listings_with_price = df_listings.merge(sorted_df_calendar, how='inner', left_on='id', right_on='listing_id')

# %% [markdown]

#  Creating new table into `df_listings_with_price` with price category
df_listings_with_price['price_category'] = pd.cut(
    df_listings_with_price['price_USD'],
    bins=[0, 100, 300, 500, float('inf')],
    labels=['Cheap', 'Medium', 'Expensive', 'Luxury']
)
df_listings_with_price


# %% [markdown]

#  Saving cleaned data into database
df_listings_with_price.to_sql('tb_silver_listings', engine, if_exists='replace', index=False)
df_calendar.to_sql('tb_silver_calendar', engine, if_exists='replace', index=False)
df_reviews.to_sql('tb_silver_reviews', engine, if_exists='replace', index=False)


# %% [markdown]

# ## Gold layer
#  Creating new dataframe for mean price by neighbourhood 
mean_price_by_neighborhood = (df_listings_with_price.groupby(['neighbourhood', 'room_type'])
                                        .agg(
                                            total_listings=('listing_id', 'nunique'),
                                            mean_price_USD=('price_USD', 'mean'),
                                            mean_price_BRL=('price_BRL', 'mean'),
                                        ).round(decimals=2)
                                        .reset_index())
mean_price_by_neighborhood

# %% [markdown]

#  Saving `mean_price_by_neighborhood` into database
mean_price_by_neighborhood.to_sql('tb_gold_neighbourhood_price', engine, if_exists='replace', index=False)


#%%
