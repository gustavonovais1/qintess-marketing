from fastapi import FastAPI
from api.api import router as api_router
from core.db import Base, engine

app = FastAPI(
    title="Qintess Marketing API",
    version="1.0",
    description="API para gerenciar e monitorar o desempenho da empresa nas midias sociais."
)
app.include_router(api_router)

def main():
    import os
    import uvicorn
    Base.metadata.create_all(bind=engine)
    port = int(os.environ.get("PORT") or 8000)
    uvicorn.run("main:app", host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
