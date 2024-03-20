from dotenv import load_dotenv
import os
import uvicorn

load_dotenv()

PORT = int(os.get('PORT', 8000))
HOST = '0.0.0.0'

if __name__ == '__main__':
    uvicorn.run('app.api:app', host = HOST, port = PORT, reload = True)