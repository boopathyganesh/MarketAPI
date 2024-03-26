from dotenv import load_dotenv
from os import getenv
import uvicorn

load_dotenv()




if __name__ == '__main__':
    PORT = int(getenv('PORT', 8000))
    HOST = '0.0.0.0'
    uvicorn.run('app.api:app', host = HOST, port = PORT, reload = True)