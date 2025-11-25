"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from case_study.api.routes import portfolios, alerts

# Create FastAPI app
app = FastAPI(
    title="Fintela Portfolio Service",
    description="REST API for managing portfolios and analytics",
    version="1.0.0",
)

# Add CORS middleware (allow all origins for development)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(portfolios.router)
app.include_router(alerts.router)


@app.get("/")
def root():
    """Root endpoint."""
    return {
        "message": "Fintela Portfolio Service API",
        "docs": "/docs",
        "version": "1.0.0"
    }


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "healthy"}

