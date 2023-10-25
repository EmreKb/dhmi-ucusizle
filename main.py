from Crypto.Util.Padding import pad
from Crypto.Cipher import AES
import requests
import base64
import re

class Location:
    
    def __init__(self, longitude, latitude, radar_date):
        self.longitude = longitude
        self.latitude = latitude
        self.radar_date =radar_date


class FlightInfo:
    
    def __init__(self, flight_id, flight_code, source_city, destination_city, source_airport, destination_airport, locations):
        self.flight_id = flight_id
        self.flight_code = flight_code
        self.source_city = source_city
        self.destination_city = destination_city
        self.source_airport = source_airport
        self.destination_airport = destination_airport
        self.locations = [Location(i["lon"], i["lat"], i["radarDate"]) for i in locations]


class DHMI:
    BASE_URL = "https://ucusizle.dhmi.gov.tr"
    ALL_FLIGHTS_URL = "https://ucusizleproxyws.dhmi.gov.tr/api/allflights"
    TRACK_URL = "https://ucusizleproxyws.dhmi.gov.tr/api/track"
    
    def __init__(self):
        self.kToken = self.get_ktoken()
    
    def get_ktoken(self):
        response = requests.get(self.BASE_URL)
        match = re.search("kToken = '(.*?)'", response.text)
        if match:
            if len(match.groups()) > 0:
                return match.groups()[0]
        raise ValueError('kToken cannot found!')
    
    def reset_token(self):
        self.kToken = self.get_ktoken()
    
    def get_all_flights(self):
        data = {"kToken": self.kToken}
        response = requests.post(self.ALL_FLIGHTS_URL, json=data)
        return response.json()
    
    def encryptTrackId(self, trackId: str):
        key = b'8056483646328763'
        iv = b'8056483646328763'

        cipher = AES.new(key, AES.MODE_CBC, iv)
        padded_data = pad(trackId.encode('utf-8'), AES.block_size)
        encrypted_data = cipher.encrypt(padded_data)
        
        encrypted_base64 = base64.b64encode(encrypted_data).decode('utf-8')

        return encrypted_base64
    
    def track(self, flight_id: str):
        data = {"kToken": self.kToken, "trackId": self.encryptTrackId(flight_id)}
        response = requests.post(self.TRACK_URL, json=data)
        return response.json()
    
    def get_flight_info(self, flight_code: str):
        all_flights = self.get_all_flights()
        flight_filter = [i["flightId"] for i in all_flights if i["flightCode"] == flight_code]
        if len(flight_filter) == 0: return
        flight_id = flight_filter[0]
        track_info = self.track(flight_id)
        return FlightInfo(track_info["flightId"], track_info["flightCode"], track_info["sourceCity"], track_info["destinationCity"], track_info["sourceAirport"], track_info["destinationAirport"], track_info["location"])
