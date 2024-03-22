import logging
import asyncio
from typing import Dict

import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse

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

# Dictionary to store scraped data
scraped_data = {}


async def scrape_data(url: str) -> Dict[str, str]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, "html.parser")
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
        return {"status": "success", "data": data_dict}
    except Exception as e:
        logger.error(f"Failed to scrape data from {url}: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch data from the website")


async def update_data():
    while True:
        await asyncio.sleep(5)
        for index_name, url in SCRAPING_URLS.items():
            try:
                scraped_data[index_name] = await scrape_data(url)
            except HTTPException as e:
                logger.error(f"HTTP Error while scraping {index_name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error while scraping {index_name}: {e}")


@app.on_event("startup")
async def startup_event():
    # Start background task to update data periodically
    asyncio.create_task(update_data())


@app.get("/")
async def home():
    return {"status": 200, "msg": "VMarket API is ONLINE"}


@app.get("/scrape/{index_name}")
async def scrape_index_data(index_name: str):
    if index_name.upper() not in SCRAPING_URLS:
        raise HTTPException(status_code=404, detail=f"Index '{index_name}' not found")

    if index_name.upper() not in scraped_data:
        raise HTTPException(status_code=500, detail=f"Data for index '{index_name}' not available")

    return JSONResponse(content=jsonable_encoder(scraped_data[index_name.upper()]))


# Error handling middleware
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content={"status": "error", "detail": exc.detail},
    )


# General exception handler
@app.exception_handler(Exception)
async def generic_exception_handler(request, exc):
    logger.error(f"An unexpected error occurred: {exc}")
    return JSONResponse(
        status_code=500,
        content={"status": "error", "detail": "An unexpected error occurred"},
    )
