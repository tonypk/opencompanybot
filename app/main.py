import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import companies, payment, mcp


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="OpenCompanyBot API",
    description="AI-powered company registration API with MCP support",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(companies.router, prefix="/api/v1/companies", tags=["companies"])
app.include_router(payment.router, prefix="/api/v1/payment", tags=["payment"])
app.include_router(mcp.router, prefix="/api/v1/mcp", tags=["mcp"])


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "opencompanybot"}


@app.get("/")
async def root():
    return {
        "name": "OpenCompanyBot API",
        "version": "0.1.0",
        "docs": "/docs",
        "mcp": "/api/v1/mcp/tools",
    }
