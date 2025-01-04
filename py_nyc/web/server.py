import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI
from py_nyc.web.api.api import router as trips_router
from fastapi.middleware.cors import CORSMiddleware
load_dotenv()
origins = [
    "http://localhost:3000"
    "https://tlc-shift.vercel.app",
    "https://tlc-shift-olci34s-projects.vercel.app"
]

server = FastAPI(debug=True)

server.add_middleware(CORSMiddleware,
                      allow_origins=origins,
                      allow_credentials=True,
                      allow_methods=["*"],
                      allow_headers=["*"])

server.include_router(trips_router)

if __name__ == '__main__':
    uvicorn.run(server, host='localhost', port=8000)
