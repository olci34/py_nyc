import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from py_nyc.web.api.api import router as trips_router

load_dotenv()

server = FastAPI(debug=True)

server.mount(
    "/static", StaticFiles(directory="./py_nyc/web/static"), name="static")

server.include_router(trips_router)

if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
