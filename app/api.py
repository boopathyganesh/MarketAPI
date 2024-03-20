import logging
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.encoders import jsonable_encoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

async def scrape_data(response):
    try:
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        element = soup.find('div', class_='indimprice')
        current_price = element.find('span', id='sp_val').text.replace(',', '')
        price_change_data = element.find('div', class_='pricupdn').text.split(" ")
        price_change = price_change_data[0].replace('\n', '')
        price_change_percentage = price_change_data[1].replace('\n', '').strip('()%')
        data_dict = {
            'current_price': current_price,
            'price_change': price_change,
            'price_change_percentage': price_change_percentage
        }
        return {"status": "success", "data": data_dict}
    except Exception as e:
        logger.error(f"Failed to scrape data: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch data from the website")


async def fetch_data(url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3',
        'Cache-Control': 'no-cache, must-revalidate'
    }
    try:
        response = requests.get(url, headers=headers)
        return response
    except Exception as e:
        logger.error(f"Failed to fetch data from {url}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch data from the website")

@app.get('/')
def home():
    return {'msg': 'VMarket API is ONLINE'}

@app.get("/scrape-BSE-500")
async def scrape_bse_500():
    url = 'https://www.moneycontrol.com/indian-indices/bse-500-12.html'
    response = await fetch_data(url)
    return jsonable_encoder(await scrape_data(response))


@app.get("/scrape-NIFTY-50")
async def scrape_nifty_50():
    url = 'https://www.moneycontrol.com/indian-indices/nifty-50-9.html'
    response = await fetch_data(url)
    return jsonable_encoder(await scrape_data(response))


@app.get("/scrape-SENSEX")
async def scrape_sensex():
    url = 'https://www.moneycontrol.com/indian-indices/sensex-4.html'
    response = await fetch_data(url)
    return jsonable_encoder(await scrape_data(response))
