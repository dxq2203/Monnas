import requests
from utils.app_exceptions import AppException

NASA_POWER_API = "https://power.larc.nasa.gov/api/temporal/daily/point"

def fetch_daily_power_data(
    start: int,
    end: int,
    longitude: float,
    latitude: float,
    community: str = "ag",
    parameters: str = "RH2M",
    format: str = "json",
    header: str = "true",
    time_standard: str = "lst"
):
    params = {
        "start": start,
        "end": end,
        "longitude": longitude,
        "latitude": latitude,
        "community": community,
        "parameters": parameters,
        "format": format.lower(),
        "header": header.lower(),
        "time-standard": time_standard.lower()
    }
    try:
        response = requests.get(NASA_POWER_API, params=params, timeout=30)
    except requests.RequestException as e:
        raise AppException.BadRequest({"error": str(e)})
    
    if response.status_code == 429:
        raise AppException.TooManyRequests(context={"nasa_status": response.status_code})

    if response.status_code >= 400:
        raise AppException.UnprocessableEntity(context={
            "nasa_status": response.status_code,
            "error": response.text
        })
    
    return response.json()
