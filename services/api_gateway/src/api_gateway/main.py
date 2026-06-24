from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api_gateway.routers import diagnostic, lesson, session, submission

app = FastAPI(title="API Gateway")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(session.router)
app.include_router(diagnostic.router)
app.include_router(lesson.router)
app.include_router(submission.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
