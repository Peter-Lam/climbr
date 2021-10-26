#!/usr/bin/python3

"""A onetime startup script to push ALL local data to a new FireStore database."""

import os
import sys

from firebase_admin import firestore

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(BASE_DIR)
import common.common as common  # noqa
import common.globals as glbs  # noqa
import config as config  # noqa


def create_locations(db):
    """
    Create location collection with the 3 local gyms.

    :param db: firestore database
    :return: Dict of location references
    :rtype: dict of ref
    """
    try:
        # Basic Location information
        locations = [
            {
                "name": "Altitude Kanata",
                "address": "0E5, 501 Palladium Dr, Kanata, ON K2V 0E5",
                "city": "Ottawa",
                "province": "Ontario",
                "country": "Canada",
                "postal": "K2V 0E5",
                "location": firestore.GeoPoint(45.297970, -75.911150),
                "grading_scale": [
                    "VB/V0",
                    "V0/V1",
                    "V1/V2",
                    "V2/V3",
                    "V3/V4",
                    "V4/V5",
                    "V5/V6",
                    "V6/V7",
                    "V7/V8",
                    "V8/V9",
                    "V9+",
                    "Kids - VB/V0",
                    "Kids - V0/V1",
                    "Kids - V1/V2",
                    "Kids - V2/V3",
                    "Kids - V3/V4",
                    "Kids - V4/V5",
                    "Kids - V5/V6",
                    "Kids - V6/V7",
                    "Kids - V7/V8",
                    "Kids - V8/V9",
                    "Kids - V9+",
                    "competition",
                    "routesetting-squad",
                ],
                "capacity": 50,
            },
            {
                "name": "Altitude Gatineau",
                "address": "35 Boulevard Saint-Raymond, Gatineau, QC J8Y 1R5",
                "city": "Gatineau",
                "province": "Quebec",
                "country": "Canada",
                "postal": "J8Y 1R5",
                "location": firestore.GeoPoint(45.446861, -75.736801),
                "grading_scale": [
                    "VB/V0",
                    "V0/V1",
                    "V1/V2",
                    "V2/V3",
                    "V3/V4",
                    "V4/V5",
                    "V5/V6",
                    "V6/V7",
                    "V7/V8",
                    "V8/V9",
                    "V9+",
                    "competition",
                    "routesetting-squad",
                ],
                "capacity": 75,
            },
            {
                "name": "Coyote Rock Gym",
                "address": "1737B St Laurent Blvd, Ottawa, ON K1G 3V4",
                "city": "Ottawa",
                "province": "Ontario",
                "country": "Canada",
                "postal": "K1G 3V4",
                "location": firestore.GeoPoint(45.406130, -75.625500),
                "grading_scale": [
                    "White",
                    "Orange",
                    "Red",
                    "Blue",
                    "Green",
                    "Purple",
                    "Black",
                    "Ungraded",
                ],
                "capacity": 50,
            },
        ]
        # Loop through locations and create a new document in firestore
        location_dict = {}
        for location in locations:
            doc_ref = db.collection("locations").document()
            location_dict[location["name"]] = doc_ref
            doc_ref.set(location)
            print(
                f"[Document ID: {doc_ref.id}] {location['name']}'s"
                " location data has been added to the db."
            )

        return location_dict
    except Exception as ex:
        raise ex


def get_locations(db):
    """
    Retrieve location data from db.

    :param db: firestore database
    :return: Dict of location references
    :rtype: dict of ref
    """
    try:
        location_dict = {}
        location_docs = db.collection("locations").get()
        for location in location_docs:
            fields = location.to_dict()
            location_dict[fields["name"]] = location
        return location_dict
    except Exception as ex:
        raise ex


def main():
    """Seting up firestore."""
    print("Connecting to db...")
    db = common.connect_to_firestore()
    # location_dict = create_locations(db)
    # If locations are already genarated use this instead
    location_dict = get_locations(db)

    # Read Bookings data
    bookings = common.load_bulk_json(os.path.join(glbs.ES_BULK_DATA, "bookings.json"))
    weather_keys = [
        "maximum_temperature",
        "minimum_temperature",
        "temperature",
        "wind_chill",
        "heat_index",
        "precipitation",
        "snow_depth",
        "wind_speed",
        "wind_gust",
        "visibility",
        "cloud_cover",
        "relative_humidity",
        "conditions",
        "weather_type",
    ]
    for booking in bookings:
        # Local variable for every booking
        weather = {}
        weather_ref = None
        # Remove and reference it to 'weather' collection if it's not already there
        if set(weather_keys).issubset(booking.keys()):
            # Move weather data to a new dict
            for key in weather_keys:
                weather[key] = booking.pop(key)
            # Copy shared information to weather document
            weather["date"] = booking["date"]
            weather["datetimestr"] = booking["datetimestr"]
            weather["city"] = booking["city"]
            # Query for existing weather data
            weather_docs = (
                db.collection("weather")
                .where("date", "==", booking["date"])
                .where("city", "==", booking["city"])
                .get()
            )
            # Reference data in bookings if exists otherwise add to weather db
            if weather_docs:
                # Get the most recent weather document that matches the date
                weather_ref = weather_docs[-1]
            # Otherwise add new weather data, and get reference
            else:
                weather_ref = db.collection("weather").document()
                weather_ref.set(weather)
                print(
                    f"[Document ID: {weather_ref.id}] {weather['city']}'s"
                    " weather data has been added to the db."
                )

        # Referencing location and weather
        booking["location_ref"] = db.collection("locations").document(
            location_dict[booking["location"]].id
        )
        booking["weather_ref"] = (
            db.collection("weather").document(weather_ref.id) if weather_ref else None
        )
        # Storing string version of their id's
        booking["location_id"] = location_dict[booking["location"]].id
        booking["weather_id"] = weather_ref.id if weather_ref else None
        # Removing Location data - No longer need because of reference
        del booking["location"]
        # Push new document to bookings collection
        booking_ref = db.collection("bookings").document()
        booking_ref.set(booking)
        print(f"[Document ID: {booking_ref.id}] Booking data has been added to the db ")
    print("Successfully added location, weather, and booking data to Firestore!")


if __name__ == "__main__":
    main()
