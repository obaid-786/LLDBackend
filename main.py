from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import problems,attempts
app = FastAPI(title="lld practice")

# allow cors for local and frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "https://your-frontend.vercel.app",   # ← replace with your Vercel URL when ready
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(problems.router)
app.include_router(attempts.router)

@app.get("/")
def root():
    return {"message": "LLD Practice Platform API"}
