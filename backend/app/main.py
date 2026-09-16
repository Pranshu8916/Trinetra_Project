from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth import router as auth_router
from app.api.health import router as health_router
from app.api.protected import router as protected_router
from app.api.screen import router as screen_router
from app.api.users import router as users_router
from app.api.verification import router as verification_router
from app.api.watchlist import router as watchlist_router
from app.core.database import database
from app.services.watchlist_service import get_watchlist_service


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        await database.users.create_index("username", unique=True)
        await database.users.create_index("user_id", unique=True)
        await database.verification_sessions.create_index("session_id", unique=True)
        await database.documents.create_index("document_id", unique=True)
        await database.documents.create_index("session_id")
        await database.document_results.create_index("document_id", unique=True)
        await database.document_results.create_index("session_id")
        await database.biometric_results.create_index("biometric_id", unique=True)
        await database.biometric_results.create_index("session_id")
        await database.verification_results.create_index("session_id", unique=True)
        # Single-shot screening reports index
        await database.screening_reports.create_index("report_id", unique=True)
        await database.screening_reports.create_index("screened_at")
        await database.screening_reports.create_index("operator_id")

        # Initialize Interpol Red Notices Watchlist cache
        get_watchlist_service()
    except Exception as error:
        print(f"Index/Service initialization warning: {error}")
    yield


app = FastAPI(
    title="Trinetra Backend",
    description="AI-powered identity verification backend",
    version="0.1.0",
    lifespan=lifespan,
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"https?://.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_cors_and_security_headers(request, call_next):
    origin = request.headers.get("origin")
    if request.method == "OPTIONS":
        from fastapi.responses import Response
        response = Response(status_code=204)
        if origin:
            response.headers["Access-Control-Allow-Origin"] = origin
            response.headers["Access-Control-Allow-Credentials"] = "true"
        else:
            response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS, PATCH"
        response.headers["Access-Control-Allow-Headers"] = "Authorization, Content-Type, Accept, Origin, User-Agent, X-Requested-With"
        return response

    response = await call_next(request)
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


from fastapi.exceptions import RequestValidationError, HTTPException
from fastapi.responses import JSONResponse
from fastapi import Request


def _apply_cors(response: JSONResponse, origin: str | None) -> JSONResponse:
    if origin:
        response.headers["Access-Control-Allow-Origin"] = origin
        response.headers["Access-Control-Allow-Credentials"] = "true"
    else:
        response.headers["Access-Control-Allow-Origin"] = "*"
    return response


@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    origin = request.headers.get("origin")
    headers = dict(exc.headers or {})
    res = JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )
    return _apply_cors(res, origin)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    origin = request.headers.get("origin")
    res = JSONResponse(
        status_code=422,
        content={"detail": exc.errors()},
    )
    return _apply_cors(res, origin)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    origin = request.headers.get("origin")
    res = JSONResponse(
        status_code=500,
        content={"detail": f"Internal Server Error: {str(exc)}"},
    )
    return _apply_cors(res, origin)

app.include_router(health_router)
app.include_router(users_router)
app.include_router(auth_router)
app.include_router(protected_router)
app.include_router(verification_router)
app.include_router(screen_router)
app.include_router(watchlist_router)
