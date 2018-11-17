from django import forms


class UserInputForm(forms.Form):
    startingPlace = forms.CharField(label='from', max_length=128)
    destinationPlace = forms.CharField(label='to', max_length=128)

