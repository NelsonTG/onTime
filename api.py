from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import json
import asyncio
import db
from main import active, order, getStops, getDelay
app = FastAPI()
activeConnect = []
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    activeConnect.append(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        activeConnect.remove(websocket)
@app.on_event("startup")
async def startup():
    try:
        db.createTable()
        print("Table created successfully")
    except Exception as e:
        print(f"createTable failed: {e}")
    asyncio.create_task(poll_loop())
    

async def poll_loop():
    while True:
        try:
            observations = getDelay()
            db.insert(observations)
            for i in activeConnect:
                await i.send_text(json.dumps(observations))
        except Exception as e:
            print(f"Polling error: {e}")
        await asyncio.sleep(30)
        
@app.get("/active")
def getActive():
    old = active()
    new = {}
    for trip_id, entity in old.items():
        new[trip_id] = {
            "route_id": entity.vehicle.trip.route_id,
            "current_status": entity.vehicle.current_status,
            "stop_id": entity.vehicle.stop_id,
            "current_stop_sequence": entity.vehicle.current_stop_sequence,
        }
    return new

@app.get("/order")
def getOrder():
    routes = order()
    def convert(train_list):
        return [
            {
                "trip_id": entity.vehicle.trip.trip_id,
                "route_id": entity.vehicle.trip.route_id,
                "current_status": entity.vehicle.current_status,
                "stop_id": entity.vehicle.stop_id,
                "current_stop_sequence": entity.vehicle.current_stop_sequence,
            }
            for entity in train_list
        ]
    for i in routes:
        routes[i] = convert(routes[i])
    return routes

@app.get("/getStops")
def getStop():
    return getStops()

@app.get("/getDelay")
def getDelays():
    return getDelay()

@app.get("/averageDelay")
def getAverageDelay():
    old = db.getAverage()
    new = {}
    for key, value in old.items():
        stop_id, route_id = key
        new_key = f"{stop_id}_{route_id}"
        new[new_key] = float(value)
    return new