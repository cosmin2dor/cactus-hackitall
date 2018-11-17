from django import forms

ATTRACTIONS_OPTIONS = [
    ('art', 'Art'),
    ('kids', 'Kids'),
    ('nature', 'Nature'),
]


class UserInputForm(forms.Form):
    startingPlace = forms.CharField(label='Departure City', max_length=128)
    destinationPlace = forms.CharField(label='Destination City', max_length=128)
    attractions = forms.MultipleChoiceField(label='Favorite attractions', widget=forms.CheckboxSelectMultiple, choices=ATTRACTIONS_OPTIONS)

