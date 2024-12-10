import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from py_nyc.web.api.api import router as trips_router
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()
origins = [
    "http://localhost",
    "http://localhost:8000",
    "http://localhost:3000",
    "https://tlc-shift.vercel.app/",
    "https://tlc-shift-olci34s-projects.vercel.app/"
]

server = FastAPI(debug=True)

server.add_middleware(CORSMiddleware,
                      allow_origins=origins,
                      allow_credentials=True,
                      allow_methods=["*"],
                      allow_headers=["*"])

server.mount(
    "/static", StaticFiles(directory="./py_nyc/web/static"), name="static")

server.include_router(trips_router)

if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
