from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers.grid_router import router

app = FastAPI(
    title="GRID — Content Model Architect",
    description="Enterprise Content Modeling & Schema Architecture Engine",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8005, reload=True)

