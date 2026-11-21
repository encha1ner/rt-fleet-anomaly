import re
from pydantic import BaseModel,Field,field_validator
from datetime import datetime
PLATE_RE=re.compile(r"^[A-Z]{2}\d{2}[A-Z]{1,3}\d{4}$")


class Telemetry(BaseModel):
    vehicle_id: str
    route_id:str
    lat:float=Field(ge=26.0,le=28.0)
    lon:float=Field(ge=80.0,le=82.0) 
    speed:float=Field(ge=0,le=200)

    
    @field_validator("vehicle_id")
    @classmethod
    def normalize_plate(cls, v: str) -> str:
        v = re.sub(r"[\s-]", "", v).upper()
        if not PLATE_RE.match(v):
            raise ValueError("invalid registration plate")
        return v


