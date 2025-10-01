from fastapi import FastAPI, APIRouter, Query, HTTPException
from fastapi.responses import JSONResponse
from utils.app_exceptions import AppExceptionCase
from services.power import fetch_daily_power_data
import requests

app = FastAPI()

router = APIRouter(prefix="/power", tags=["NASA POWER API"])

@router.get("/api/temporal/daily/point")
async def proxy_nasa_power_daily_point(
    start: int = Query(..., description="Start date in YYYYMMDD format"),
    end: int = Query(..., description="End date in YYYYMMDD format"),
    longitude: float = Query(..., description="Longitude of the point"),
    latitude: float = Query(..., description="Latitude of the point"),
    community: str = Query("ag", description="Community: ag / re / sb"),
    parameters: str = Query("RH2M", description="Comma-separated parameters, e.g. RH2M,T2M"),
    format: str = Query("json", description="Response format: json, csv, etc."),
    header: str = Query("true", description="Include header (true/false)"),
    time_standard: str = Query("lst", alias="time-standard", description="Time standard: lst or utc")
):
    """
    Proxy endpoint to NASA POWER API daily point service.
    It constructs a request like:

    https://power.larc.nasa.gov/api/temporal/daily/point
    """

    try:
        return fetch_daily_power_data(
            start=start,
            end=end,
            longitude=longitude,
            latitude=latitude,
            community=community,
            parameters=parameters,
            format=format,
            header=header,
            time_standard=time_standard
        )
    except AppExceptionCase as e:
        return JSONResponse(
            status_code=e.status_code,
            content={"error": e.exception_case, "context": e.context}
        )

