import logging
import asyncio
import requests
from bs4 import BeautifulSoup
from fastapi import FastAPI, HTTPException, BackgroundTasks
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

# Global variable to store scraped data
scraped_data = {}


def scrape_data(url: str) -> dict:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3",
        "Cache-Control": "no-cache, must-revalidate",
    }
    try:
        response = requests.get(url, headers=headers)
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
        return data_dict
    except Exception as e:
        logger.error(f"Failed to scrape data from {url}: {e}")
        return {}


async def update_data():
    global scraped_data
    while True:
        for index_name, url in SCRAPING_URLS.items():
            scraped_data[index_name] = scrape_data(url)
            print(scraped_data)
        await asyncio.sleep(5)


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(update_data())


@app.get("/")
async def home():
    return {"status": 200, "msg": "VMarket API is ONLINE"}


@app.get("/scrape/{index_name}")
async def scrape_index_data(index_name: str):
    if index_name.upper() not in SCRAPING_URLS:
        raise HTTPException(status_code=404, detail=f"Index '{index_name}' not found")

    if not scraped_data.get(index_name):
        raise HTTPException(status_code=500, detail="Data not available")

    return JSONResponse(content=scraped_data[index_name])


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
