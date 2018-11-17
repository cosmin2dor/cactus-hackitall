from django.shortcuts import render
from .forms import UserInputForm


def index(request):
    if request.method == 'POST':
        form = UserInputForm(request.POST)
        # return render(request, "index.html", {'form': form})
    else:
        form = UserInputForm()
        # return render(request, "index.html", {})

    if form.is_valid():
        print("form is valid")
        source = form.cleaned_data['startingPlace']
        destination = form.cleaned_data['destinationPlace']


        print(source + " " + destination)

    return render(request, "index.html", {'form': form})
