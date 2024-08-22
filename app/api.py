import logging
import random
import aiohttp
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Logging configuration
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# FastAPI app
app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust this to your frontend URL when in production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["https://www.value1.in/","http://127.0.0.1:8000/"],
)

# Constants
SCRAPING_URLS = {
    "BSE-500": "https://www.moneycontrol.com/indian-indices/bse-500-12.html",
    "NIFTY-50": "https://www.moneycontrol.com/indian-indices/nifty-50-9.html",
    "SENSEX": "https://www.moneycontrol.com/indian-indices/sensex-4.html",
}


async def scrape_data(url: str) -> dict:
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            raw_data = await response.read()
            try:
                response_text = raw_data.decode('utf-8')
            except UnicodeDecodeError:
                response_text = raw_data.decode('latin1')  # Fallback to latin1 encoding if utf-8 fails

            soup = BeautifulSoup(response_text, "html.parser")
            element = soup.find("div", class_="indimprice")
            if not element:
                logger.warning(f"Failed to find the element on the page: {url}")
                return {}

            try:
                current_price = element.find("span", id="sp_val").text.replace(",", "")
                price_change_data = element.find("div", class_="pricupdn").text.split(" ")
                price_change = price_change_data[0].replace("\n", "")
                price_change_percentage = price_change_data[1].replace("\n", "").strip("()%")
                data_dict = {
                    "current_price": current_price,
                    "price_change": price_change,
                    "price_change_percentage": price_change_percentage,
                }
                #logger.info(f"Scraped data: {data_dict}")
                return data_dict
            except AttributeError as e:
                logger.warning(f"Attribute error when parsing the page: {url}, error: {e}")
                return {}


@app.get("/")
async def home():
    return {"status": 200, "msg": "VMarket is ONLINE"}


@app.get("/scrape")
async def scrape_all_indices():
    scraped_data = {}
    for index_name, url in SCRAPING_URLS.items():
        data = await scrape_data(url)
        if not data:
            logger.warning(f"Failed to scrape data for {index_name}")
        else:
            scraped_data[index_name] = data

    if not scraped_data:
        raise HTTPException(status_code=500, detail="Failed to scrape data for any index")

    return scraped_data


# Error handling middleware
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"status": "error", "detail": exc.detail}


# General exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"An unexpected error occurred: {exc}")
    return {"status": "error", "detail": "An unexpected error occurred"}
