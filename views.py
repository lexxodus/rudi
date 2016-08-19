from __future__ import unicode_literals
from datetime import date
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render
from rudi.forms import RegistrationForm
from rudi import mails
from rudi.models import Event, Team


def registration(request):
    try:
        event = Event.objects.get(active=True)
    except:
        return render(request, "rudi/disabled.html")
    if event.end_registration < date.today():
        event.active = False
        event.save()
        return render(request, "rudi/disabled.html")
    dyn_desc = event.get_dynamic_desc(request.LANGUAGE_CODE)
    registration = Team(event=event)
    if request.method == "POST":
        form = RegistrationForm(request.POST, instance=registration)
        if form.is_valid():
            team = form.save(commit=False)
            if request.LANGUAGE_CODE == "de":
                team.language = request.LANGUAGE_CODE
            else:
                team.language = "en"
            team.save()
            form.save_m2m()
            mails.send_code(request, team)
            return render(request, "rudi/registered.html", {
                "event": event,
                "email": form.cleaned_data["participant_1_email"],
            })
    else:
        form = RegistrationForm()
    return render(request, "rudi/registration.html", {
        'form': form,
        'event': event,
        'dyn_desc': dyn_desc,
    })


def confirm_email(request, code):
    try:
        team = Team.objects.get(code=code)
    except ObjectDoesNotExist:
        return render(request, 'rudi/code_denied.html')
    else:
        event = team.event
        if team.has_confirmed_email:
            return render(
                request,
                'rudi/code_already_confirmed.html', {
                    'event': event,
                })
        else:
            team.has_confirmed_email = True
            team.save()
            return render(
                request,
                'rudi/code_confirmed.html', {
                    'event': event,
                })
