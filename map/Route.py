import requests, json
from geopy.geocoders import Nominatim
import xml.etree.ElementTree as xml
import numpy as np


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
    coords = [(source.lat, source.lon), (dest.lat, dest.lon)]
    url = "https://router.project-osrm.org/route/v1/driving/"

    params = ""

    for (lat, lon) in coords:
        params += str(lat) + "," + str(lon) + ";"

    params = params[:-1]

    print(url + params)

    response = requests.get(url + params)

    # Print the status code of the response.
    print(str(response.status_code) + " status code\n")

    my_json = json.loads(response.text)

    i = my_json.get('routes')

    distance = i.get('distance')    # float meters
    duration = i.get('duration')    # float number of seconds

    return distance, duration

stops = []

class Route:

    def __init__(self, source, destination, max_hops, max_time):
        geolocator = Nominatim()
        self.source = geolocator.geocode(source)
        self.destination = geolocator.geocode(destination)
        self.max_hops = max_hops
        self.max_time = max_time

    # icons
    # 0 - SOURCE
    # 1 - DESTINATION
    # 2 - CHARGING
    # 3 - ATTRACTION
    # 4 - HOTEL

    def start(self):
        # Initial route setup
        start_place = Place("Departure Place", Waypoint(self.source.latitude, self.source.longitude), "You are going to leave this place.", 0)
        destination_place = Place("Arrival Place", Waypoint(self.destination.latitude, self.destination.longitude), "Your destination, so that you know that.", 1)

        start_stop = Stop(start_place, 0.0, 0.0, 100.0, self.max_hops)
        destination_stop = Stop(destination_place, self.max_time, 0.0, 0.0, 0)

        stops = [start_stop, destination_stop]

        s = np.array([start_place.position.lat, start_place.position.lon])
        d = np.array([destination_place.position.lat, destination_place.position.lon])

        distance = np.linalg.norm(s - d)
        direction = (d - s) / distance

        mid_point = s + direction * (distance / self.max_hops)

        kk = 100
        while kk:
            print(getAround(mid_point[0], mid_point[1], 50000, 'attraction'))
            kk = kk - 1

        # newPlace = Place("blabla", Waypoint(newPos[0], newPos[1]), "", 2)
        # newStop = Stop(newPlace, 0.0, 0.0, 0, 0)
        # stops.append(newStop)

        return stops



class Waypoint:

    def __init__(self, lat, lon):
        self.lat = lat
        self.lon = lon


class Stop:

    def __init__(self, place, current_time, waiting_time, current_battery, hops):
        self.place = place
        self.current_time = current_time
        self.waiting_time = waiting_time
        self.current_battery = current_battery
        self.hops = hops


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
