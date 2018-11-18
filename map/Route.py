from pprint import pprint

import requests, json
from geopy.geocoders import Nominatim
import xml.etree.ElementTree as xml
import numpy as np

from .models import Attraction as A
from .models import ChargingStation as C
from .models import Hotel as H

from math import sin, cos, sqrt, atan2, radians

import base64
from io import BytesIO

import qrcode
import random

from datetime import datetime, timedelta

R = 6373.0
CAR_CONSUMPTION = 0.175

preferences_dict = {
    'art': ['artwork', 'attraction', 'gallery', 'museum'],
    'kids': ['aquarium', 'attraction', 'theme_park', 'zoo'],
    'nature': ['attraction'],
}


def parseXML(e, type):
    for node in e.findall('node'):
        name = ""
        lat = node.attrib["lat"]
        lon = node.attrib["lon"]
        description = ""
        attraction_type = ""
        rate = None
        voltage = 120
        amperage = 5

        attraction = False
        hotel = False
        chargingStation = False

        # get type
        for tag in node:
            if tag.attrib["k"] == "name":
                name = tag.attrib["v"]

            if tag.attrib["k"] == "amenity" and tag.attrib["v"] == "charging_station":
                chargingStation = True

            if tag.attrib["k"] == "tourism" and tag.attrib["v"] == "hotel":
                hotel = True

            if tag.attrib["k"] == "tourism" and tag.attrib["v"] != "hotel":
                attraction = True

        # set variables
        if name != "":
            if chargingStation and type == "station":
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "voltage":
                        voltage = tag.attrib["v"]

                    if tag.attrib["k"] == "amperage":
                        amperage = tag.attrib["v"]
                print("ti-am dat statie")
                return name
            elif hotel and type == "hotel":
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "stars":
                        rate = tag.attrib["v"]

                print("ti-am dat hotel")
                return name
            elif attraction and type == "attraction":
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "stars":
                        rate = tag.attrib["v"]

                    if tag.attrib["k"] == "tourism":
                        attraction_type = tag.attrib["v"]
                print("ti-am dat atractie")
                return name


def generateXML(query):
    r = requests.post('http://overpass-api.de/api/interpreter', data=query)

    print(r.status_code)

    return r.text


def getAround(lat, lon, radius, type):
    query_xml = ""

    if type == "hotel":
        query_xml = """
<query type="node">
<around lat=\"""" + str(lat) + "\" lon=\"" + str(lon) + "\" radius=\"" + str(radius) + "\"/>" + """
<has-kv k="tourism" v="hotel"/>
</query>
<print />
"""
    elif type == "station":
        query_xml = """
<query type="node">
<around lat=\"""" + str(lat) + "\" lon=\"" + str(lon) + "\" radius=\"" + str(radius) + "\"/>" + """
<has-kv k="amenity" v="charging_station"/>
</query>
<print />
"""
    elif type == "attraction":
        query_xml = """
<query type="node">
<around lat=\"""" + str(lat) + "\" lon=\"" + str(lon) + "\" radius=\"" + str(radius) + "\"/>" + """
<has-kv k="tourism"/>
</query>
<print />
"""

    response = generateXML(query_xml)

    return parseXML(xml.ElementTree(xml.fromstring(response)), type)


def get_route_details(source, dest):
    coords = [(source.lon, source.lat), (dest.lon, dest.lat)]
    # TODO Change with OSRM server
    url = "http://192.168.43.188:5000/route/v1/driving/"

    params = ""

    for (lat, lon) in coords:
        params += str(lat) + "," + str(lon) + ";"

    params = params[:-1]

    response = requests.get(url + params)

    my_json = json.loads(response.text)

    i = my_json.get('routes')

    if i is None:
        distance = 10
        duration = 0.5
    else:
        distance = i[0].get('distance')  # float meters
        duration = i[0].get('duration')  # float number of seconds

    return distance / 1000.0, duration

def getCoords(name):
    url = "https://nominatim.openstreetmap.org/?format=json&city="

    response = requests.get(url + name)
    my_json = json.loads(response.text)

    return [float(my_json[0].get('lat')), float(my_json[0].get('lon'))]

def getAddress(lat, lon):
    url = "https://nominatim.openstreetmap.org/reverse?format=json&lat="

    url += str(lat) + '&lon=' + str(lon) + '&zoom=18'

    response = requests.get(url)

    # Print the status code of the response.
    print(str(response.status_code) + " status code\n")

    my_json = json.loads(response.text)

    pprint(my_json)

    location = my_json.get('address').get('city')

    if location is None:
        location = my_json.get('address').get('village')

    return location


def getQR(waypoints):
    url = "https://www.google.com/maps/dir/?api=1&origin=" + str(waypoints[0][0]) + "," + str(waypoints[0][1]) + '&destination=' + str(waypoints[-1][0]) + "," + str(waypoints[-1][1]) + '&travelmode=driving'

    if len(waypoints) > 2:
        url += '&waypoints='
        for waypoint in waypoints[1:-1]:
            url += str(waypoint[0]) + "," + str(waypoint[1]) + "%7C"

    url = url[:-3]

    return url

def shortenURL(url):
    r = requests.post("https://api.rebrandly.com/v1/links",
                      data=json.dumps({
                          "destination": str(url)
                          , "domain": {"fullName": "rebrand.ly"}
                      }),
                      headers={
                          "Content-type": "application/json",
                          "apikey": "e7d5f406806448ab893e75a81f79ebf2",
                      })

    if r.status_code == requests.codes.ok:
        link = r.json()

        return str(link["shortUrl"])


class Route:

    def __init__(self, source, destination, max_hops, max_time, max_capacity):
        self.source = getCoords(source)
        self.destination = getCoords(destination)
        self.max_hops = max_hops
        self.max_time = max_time
        self.max_capacity = max_capacity
        self.stops = []
        self.visited_a = []
        self.visited_c = []
        self.visited_h = []
        self.uptime = 0
        self.offset = 0

    # icons
    # 0 - SOURCE
    # 1 - DESTINATION
    # 2 - CHARGING
    # 3 - ATTRACTION
    # 4 - HOTEL

    @staticmethod
    def image_to_base64(image):
        output = BytesIO()
        image.save(output, format="PNG")
        image_data = output.getvalue()

        return base64.b64encode(image_data).decode('utf-8')

    def generate_QR(self, waypoints_coords):
        w_list = []
        for w in waypoints_coords:
            w_list.append((w.place.position.lat, w.place.position.lon))

        url = getQR(w_list)
        qr_img = qrcode.make(shortenURL(url))
        return Route.image_to_base64(qr_img)

    @staticmethod
    def distance_between(a, b):
        dlon = radians(b.lon) - radians(a.lon)
        dlat = radians(b.lat) - radians(a.lat)

        d = sin(dlat / 2) ** 2 + cos(radians(a.lat)) * cos(radians(b.lat)) * sin(dlon / 2) ** 2
        c = 2 * atan2(sqrt(d), sqrt(1 - d))
        return R * c

    def get_nearest(self, position, radius, type):
        types = ['attraction']
        for i in self.attraction_prefs:
            types = types + preferences_dict[i]

        if type == "Attraction":
            for a in A.objects.all():
                if a.pk in self.visited_a or a.type not in types:
                    continue
                elif Route.distance_between(a, position) < radius:
                    self.visited_a.append(a.pk)
                    return a
            return self.get_nearest(position, radius + 10, type)
        elif type == "ChargingStation":
            min_distance = 9999
            nearest_station = None
            for s in C.objects.all():
                distance = Route.distance_between(s, position)
                if distance < min_distance:
                    if s.pk not in self.visited_c:
                        min_distance = distance
                        nearest_station = s

            self.visited_c.append(nearest_station.pk)
            return nearest_station
        elif type == "Hotel":
            min_distance = 9999
            nearest_hotel = None
            for h in H.objects.all():
                distance = Route.distance_between(h, position)
                if distance < min_distance:
                    if h.pk not in self.visited_h:
                        min_distance = distance
                        nearest_hotel = h

            self.visited_h.append(nearest_hotel.pk)
            return nearest_hotel


    def is_battery_reachable(self, current_stop):
        nearest_station = self.get_nearest(current_stop.place.position, 0, "ChargingStation")
        (distance, duration) = get_route_details(current_stop.place.position, Waypoint(nearest_station.lat, nearest_station.lon))

        range_available = ((current_stop.current_battery / 100.0) * self.max_capacity) / CAR_CONSUMPTION
        if range_available < distance:
            return False
        else:
            return True



    def start(self, attraction_prefs):
        self.attraction_prefs = attraction_prefs
        # Initial route setup
        start_place = Place("Departure Place", Waypoint(self.source[0], self.source[1]), "You are going to leave this place.", "S")
        destination_place = Place("Arrival Place", Waypoint(self.destination[0], self.destination[1]), "Your destination, so that you know that.", "D")

        (total_distance, total_duration) = get_route_details(start_place.position, destination_place.position)
        energy_consumption = CAR_CONSUMPTION * total_distance

        total_chr_time = ((energy_consumption - self.max_capacity) * (248 * 96)) / 3600 + 1

        if total_chr_time < 0:
            total_chr_time = 0

        while self.max_time - total_chr_time - self.max_hops - total_duration / 3600 < 0:
            self.max_hops = self.max_hops - 1

        start_stop = Stop(start_place, 0.0, 100.0, self.max_hops)
        destination_stop = Stop(destination_place, 0.0, 0, 0)

        self.stops = [start_stop]

        # Starting the recursion
        exit = self.recursion(start_stop, destination_stop)
        if exit == -1:
            return -1
        self.stops.append(destination_stop)

        return self.stops

    def recursion(self, start_stop, end_stop):
        s = np.array([start_stop.place.position.lat, start_stop.place.position.lon])
        d = np.array([end_stop.place.position.lat, end_stop.place.position.lon])

        distance = Route.distance_between(start_stop.place.position, end_stop.place.position)
        direction = (d - s) / distance

        if self.offset == 0:
            self.offset = distance / self.max_hops

        mid_point = s + direction * self.offset

        nearest_attraction = self.get_nearest(Waypoint(mid_point[0], mid_point[1]), 10, "Attraction")
        (distance_to, duration_to) = get_route_details(start_stop.place.position, Waypoint(nearest_attraction.lat, nearest_attraction.lon))
        self.uptime = self.uptime + duration_to / 3600

        new_place = Place(nearest_attraction.name, Waypoint(nearest_attraction.lat, nearest_attraction.lon), nearest_attraction.description, "A")
        new_stop = Stop(new_place, start_stop.departure_time + (duration_to / 3600), start_stop.current_battery - ((distance_to * CAR_CONSUMPTION) / self.max_capacity) * 100, start_stop.hops - 1)
        new_stop.randomize_wait(0.5, 1.0)

        if not self.is_battery_reachable(new_stop):
            nearest_station = self.get_nearest(start_stop.place.position, 0, "ChargingStation")
            new_place = Place(nearest_station.name, Waypoint(nearest_station.lat, nearest_station.lon), nearest_station.description, "C")
            (distance_to, duration_to) = get_route_details(start_stop.place.position, Waypoint(nearest_station.lat, nearest_station.lon))
            self.uptime = self.uptime + duration_to / 3600
            new_stop = Stop(new_place, start_stop.departure_time + (duration_to / 3600),
                            start_stop.current_battery - ((distance_to * CAR_CONSUMPTION) / self.max_capacity) * 100,
                            start_stop.hops - 1)
            # new_stop.fuel_time(nearest_station.voltage, nearest_station.amperage, self.max_capacity)
            new_stop.fuel_time(240, 96, self.max_capacity)
        elif self.uptime >= 8:
            nearest_hotel = self.get_nearest(start_stop.place.position, 0, "Hotel")
            new_place = Place(nearest_hotel.name, Waypoint(nearest_hotel.lat, nearest_hotel.lon), nearest_hotel.description, "H")
            (distance_to, duration_to) = get_route_details(start_stop.place.position,
                                                           Waypoint(nearest_hotel.lat, nearest_hotel.lon))
            self.uptime = 0
            new_stop = Stop(new_place, start_stop.departure_time + (duration_to / 3600),
                            start_stop.current_battery - ((distance_to * CAR_CONSUMPTION) / self.max_capacity) * 100,
                            start_stop.hops - 1)
            new_stop.sleep()

        if new_stop.current_battery <= 0:
            return -1

        self.stops.append(new_stop)

        if new_stop.hops > 0:
            self.recursion(new_stop, end_stop)
        else:
            (distance_to, duration_to) = get_route_details(new_stop.place.position, end_stop.place.position)
            end_stop.current_time = new_stop.departure_time + (duration_to / 3600)
            end_stop.current_battery = new_stop.current_battery - ((distance_to * CAR_CONSUMPTION) / self.max_capacity) * 100
            end_stop.departure_time = end_stop.current_time
            end_stop.format_dates()

            if end_stop.current_battery <= 0:
                return -1
            return


class Waypoint:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


class Stop:

    def __init__(self, place, current_time, current_battery, hops):
        self.place = place
        self.current_time = current_time
        self.current_battery = current_battery
        self.hops = hops
        self.departure_time = current_time
        self.formated_arrival = datetime.now()
        self.formated_departure = datetime.now()

    def format_dates(self):
        self.formated_arrival = datetime.now() + timedelta(hours=self.current_time)
        self.formated_departure = datetime.now() + timedelta(hours=self.departure_time)

    def randomize_wait(self, a, b):
        self.waiting_time = random.randrange(int(a*10), int(b*10)) / 10
        self.departure_time = self.current_time + self.waiting_time
        self.format_dates()

    def fuel_time(self, volts, amps, max_capacity):
        till_full = (1.0 - (self.current_battery / 100)) * max_capacity
        charging_time = till_full / ((volts * amps) / 1000)
        self.departure_time = self.current_time + charging_time
        print("Charging Time" + self.current_battery.__str__())
        self.current_battery = 100
        self.format_dates()

    def sleep(self):
        self.departure_time = self.current_time + 6.0
        self.format_dates()

class Place:

    def __init__(self, name, position, description, icon):
        self.name = name
        self.position = position
        self.description = description
        self.icon = icon


class Attraction(Place):

    def __init__(self, name, position, description, icon, type):
        Place.__init__(name, position, description, icon)
        self.type = type


class Hotel(Place):

    def __init__(self, name, position, description, icon, rate):
        Place.__init__(name, position, description, icon)
        self.rate = rate


class ChargingStation(Place):

    def __init__(self, name, position, description, icon, voltage, amperage):
        Place.__init__(name, position, description, icon)
        self.voltage = voltage
        self.amperage = amperage
