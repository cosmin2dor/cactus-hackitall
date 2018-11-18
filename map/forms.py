from django import forms

ATTRACTIONS_OPTIONS = [
    ('art', 'Art'),
    ('kids', 'Kids'),
    ('nature', 'Nature'),
]


class UserInputForm(forms.Form):
    startingPlace = forms.CharField(label='Departure City', max_length=128)
    destinationPlace = forms.CharField(label='Destination City', max_length=128)
    numberOfHours = forms.IntegerField(label='Number of hours', widget=forms.NumberInput, min_value=0)
    maxNumberOfStops = forms.IntegerField(label='Max number of stops', widget=forms.NumberInput, min_value=0)
    batteryCapacity = forms.IntegerField(label='Your car\'s battery capacity (kWh)', widget=forms.NumberInput, min_value=0, max_value=120)
    attractions = forms.MultipleChoiceField(required=False, label='Favorite attractions', widget=forms.CheckboxSelectMultiple, choices=ATTRACTIONS_OPTIONS)

