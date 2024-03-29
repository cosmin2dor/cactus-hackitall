import xml.etree.ElementTree as xml

from django.shortcuts import render
from .forms import UserInputForm

from .models import Attraction, ChargingStation, Hotel
from .Route import Route, Waypoint


def fix_duplicates(request):
    for c1 in ChargingStation.objects.all():
        for c2 in ChargingStation.objects.all():
            if c1.pk == c2.pk:
                continue
            distance = Route.distance_between(Waypoint(c1.lat, c1.lon), Waypoint(c2.lat, c2.lon))
            print(distance)

    return render(request, "index.html", {'form': UserInputForm()})


def populate_database(request):
    Attraction.objects.all().delete()
    Hotel.objects.all().delete()
    ChargingStation.objects.all().delete()

    e = xml.parse('map/database.osm').getroot()

    for node in e.findall('node'):
        name = ""
        default_station_name = "Charging Station"
        lat = node.attrib["lat"]
        lon = node.attrib["lon"]
        description = ""
        attraction_type = ""
        rate = 0
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
                name = default_station_name
                chargingStation = True

            # if tag.attrib["k"] == "tourism" and (tag.attrib["v"] == "hotel" or tag.attrib["v"] == "guest_house" or tag.attrib["v"] == "hostel" or tag.attrib["v"] == "chalet" or tag.attrib["v"] == "camp_site" or tag.attrib["v"] == "apartment" or tag.attrib["v"] == "motel" or tag.attrib["v"] == "caravan_site"):
            #     hotel = True

            if tag.attrib["k"] == "tourism" and tag.attrib["v"] == "hotel":
                hotel = True

            if tag.attrib["k"] == "tourism" and (tag.attrib["v"] == "zoo" or tag.attrib["v"] == "aquarium" or tag.attrib["v"] == "artwork" or tag.attrib["v"] == "attraction" or tag.attrib["v"] == "gallery" or tag.attrib["v"] == "museum" or tag.attrib["v"] == "theme_park" or tag.attrib["v"] == "zoo"):
                attraction = True

        # set variables
        if name != "":
            if chargingStation:
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "voltage":
                        voltage = tag.attrib["v"]

                    if tag.attrib["k"] == "amperage":
                        amperage = tag.attrib["v"]

                ChargingStation.objects.create(name=name, lat=lat, lon=lon, description=description, voltage=voltage, amperage=amperage)
            elif hotel:
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "stars":
                        rate = tag.attrib["v"]

                Hotel.objects.create(name=name, lat=lat, lon=lon, rate=rate, description=description)

            elif attraction:
                for tag in node:
                    if tag.attrib["k"] == "description":
                        description = tag.attrib["v"]

                    if tag.attrib["k"] == "tourism":
                        attraction_type = tag.attrib["v"]
                Attraction.objects.create(name=name, lat=lat, lon=lon, description=description, type=attraction_type)

    print("Database Populated Successfully")
    return render(request, "index.html", {'form': UserInputForm()})


def index(request):
    if request.method == 'POST':
        form = UserInputForm(request.POST)
    else:
        form = UserInputForm()

    stops = []
    qr = ""

    if form.is_valid():
        source = form.cleaned_data['startingPlace']
        destination = form.cleaned_data['destinationPlace']
        max_hops = form.cleaned_data['maxNumberOfStops']
        max_hours = form.cleaned_data['numberOfHours']
        capacity = form.cleaned_data['batteryCapacity']
        attractions = form.cleaned_data['attractions']
        route = Route(source, destination, max_hops, max_hours, capacity)
        stops = route.start(attractions)

        if stops == -1:
            return render(request, "index.html", {'form': UserInputForm()})
        else:
            qr = route.generate_QR(stops)

    return render(request, "index.html", {'form': form,
                                          'stops': stops,
                                          'qr_link': qr})
