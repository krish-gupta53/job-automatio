from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from workflow import router

app = FastAPI(title="CreatorPilot AI", version="0.2.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
