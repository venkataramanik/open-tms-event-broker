import json
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
import pika

app = FastAPI(title="Open TMS Event Broker API")

def get_rmq_channel():
    try:
        connection = pika.BlockingConnection(pika.ConnectionParameters(host='rabbitmq'))
        channel = connection.channel()
        channel.queue_declare(queue='tms_events', durable=True)
        return connection, channel
    except Exception:
        raise HTTPException(status_code=503, detail="Message broker offline")

class TMSEvent(BaseModel):
    event_id: str = Field(..., examples=["TRK-9901"])
    event_type: str = Field(..., examples=["SHIPMENT_DEPARTED", "CARRIER_GEO_PING"])
    facility_id: str = Field(..., examples=["DC-SAVANNAH"])
    payload: dict

@app.post("/api/v1/events", status_code=status.HTTP_202_ACCEPTED)
async def ingest_event(event: TMSEvent):
    connection, channel = get_rmq_channel()
    channel.basic_publish(
        exchange='',
        routing_key='tms_events',
        body=json.dumps(event.model_dump()),
        properties=pika.BasicProperties(delivery_mode=2)
    )
    connection.close()
    return {"status": "Accepted", "message": "TMS tracking event queued"}

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "Open TMS Gateway"}
