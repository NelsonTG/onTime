import httpx, csv
from datetime import datetime
from google.transit import gtfs_realtime_pb2 as gtfs
feedAPI = [
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-ace",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-g",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-bdfm",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-jz",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-nqrw",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-l",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs",
    "https://api-endpoint.mta.info/Dataservice/mtagtfsfeeds/nyct%2Fgtfs-si",
]

def fetch(url):
    data = httpx.get(url)
    data.raise_for_status()
    feed = gtfs.FeedMessage()
    feed.ParseFromString(data.content)
    return feed

def active():
    trains = {}
    for i in feedAPI:
        feed = fetch(i)
        for j in feed.entity:
            if j.vehicle:
                trains[j.vehicle.trip.trip_id] = j
    return trains


def tripUpdates():
    updates = {}
    for i in feedAPI:
        feed = fetch(i)
        for j in feed.entity:
            if j.trip_update:
                updates[j.trip_update.trip.trip_id] = j
    return updates


def order():
    trains = active()
    routes = {}
    for i in trains:
        route_id = trains[i].vehicle.trip.route_id
        routes.setdefault(route_id, []).append(trains[i])
    for route_id in routes:
        routes[route_id] = sorted(routes[route_id], key=lambda entity: entity.vehicle.current_stop_sequence)
    return routes

def loadStopTimes():
    stop_times = {}
    with open("gtfs_subway/stop_times.txt") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stop_id = row["stop_id"]
            stop_times.setdefault(stop_id, []).append(row["arrival_time"])
    return stop_times


def getStops():
    stops = {}
    with open("gtfs_subway/stops.txt") as f:
        reader = csv.DictReader(f)
        for row in reader:
            stops[row["stop_id"]] = row["stop_name"]
    return stops


def getDelay():
    def getTime(start_date, time_str):
        year = int(start_date[0:4])
        month = int(start_date[4:6])
        day = int(start_date[6:8])
        hour, minute, second = map(int, time_str.split(":"))
        extraDays = hour // 24
        hour = hour % 24
        dt = datetime(year, month, day, hour, minute, second)
        timestamp = dt.timestamp()
        if extraDays:
            timestamp += extraDays * 86400
        return timestamp

    updates = tripUpdates()
    stopsTimes = loadStopTimes()
    observations = []

    for trip_id, entity in updates.items():
        start_date = entity.trip_update.trip.start_date
        route_id = entity.trip_update.trip.route_id
        for stop_update in entity.trip_update.stop_time_update:
            stop_id = stop_update.stop_id
            actual_ts = stop_update.arrival.time
            candidates = stopsTimes.get(stop_id, [])
            best_diff = None
            best_ts = None
            for time_str in candidates:
                try:
                    scheduled_ts = getTime(start_date, time_str)
                except ValueError:
                    continue
                diff = abs(actual_ts - scheduled_ts)
                if best_diff is None or diff < best_diff:
                    best_diff = diff
                    best_ts = scheduled_ts
            if best_ts is not None and best_diff < 3600:
                observations.append({
                    "trip_id": trip_id,
                    "stop_id": stop_id,
                    "route_id": route_id,
                    "delay_seconds": actual_ts - best_ts,
                    "scheduled_ts": best_ts,
                    "actual_ts": actual_ts,
                })

    return observations


if __name__ == "__main__":
    pass