import logging
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
    allow_headers=["*"],
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
            response_text = await response.text()
            soup = BeautifulSoup(response_text, "html.parser")
            element = soup.find("div", class_="indimprice")
            current_price = element.find("span", id="sp_val").text.replace(",", "")
            price_change_data = element.find("div", class_="pricupdn").text.split(" ")
            price_change = price_change_data[0].replace("\n", "")
            price_change_percentage = price_change_data[1].replace("\n", "").strip("()%")
            data_dict = {
                "current_price": current_price,
                "price_change": price_change,
                "price_change_percentage": price_change_percentage,
            }
            return data_dict


@app.get("/")
async def home():
    return {"status": 200, "msg": "VMarket API is ONLINE"}


@app.get("/scrape/{index_name}")
async def scrape_index_data(index_name: str):
    url = SCRAPING_URLS.get(index_name.upper())
    if not url:
        raise HTTPException(status_code=404, detail=f"Index '{index_name}' not found")

    scraped_data = await scrape_data(url)
    if not scraped_data:
        raise HTTPException(status_code=500, detail="Failed to scrape data")

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