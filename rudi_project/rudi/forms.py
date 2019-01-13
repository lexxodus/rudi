# -*- coding: UTF-8 -*-
from .models import Team
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

LABEL_STREET = _("Straße")
LABEL_POSTAL_CODE = _("PLZ")
LABEL_CITY = _("Stadt")
LABEL_DOORBELL = _("Klingelinfo")
LABEL_FIRSTNAME = _("Vorname")
LABEL_LASTNAME = _("Nachname")
LABEL_EMAIL = _("E-Mail")
LABEL_PHONE = _("Handynummer")
LABEL_ALLERGIES = _("Allergien/ Unverträglichkeiten")
LABEL_LIKE = _("Wir würden am liebsten diesen Gang/ einen dieser Gänge "
               "zubereiten")
LABEL_DISLIKE = _("Wir würden diesen Gang/ einen dieser Gänge lieber "
                  "nicht zubereiten")
LABEL_AGREE_TERMS = _("Teilnahmebedingungen")

INFO_NAME = _("Seid kreativ!")
INFO_DOORBELL = _("Gebt an, wo eure Gäste klingeln müssen und "
                  "in welches Stockwerk sie müssen")
INFO_AGREE_TERMS = _("Hiermit erklärt ihr euch einverstanden, dass wir "
                     "eure Handynummern an die Teams weiterleiten dürfen, "
                     "mit denen ihr gemeinsam essen werdet.")


ERROR_AGREE_TERMS =\
    _('Du musst mit der weitergabe deiner/ eurer Handynummern '
      'einverstanden sein.')
ERROR_PREFERENCES = _('Du kannst den selben Kurs nicht in beiden Listen haben')


class RegistrationForm(forms.ModelForm):

    agree_terms = forms.BooleanField(
        label=LABEL_AGREE_TERMS,
        help_text=INFO_AGREE_TERMS,
        error_messages={
            'required': ERROR_AGREE_TERMS
        })

    class Meta:
        model = Team
        exclude = ("event",)
        labels = {
            "street": LABEL_STREET,
            "postal_code": LABEL_POSTAL_CODE,
            "city": LABEL_CITY,
            "doorbell": LABEL_DOORBELL,
            "participant_1_firstname": LABEL_FIRSTNAME,
            "participant_2_firstname": LABEL_FIRSTNAME,
            "participant_1_lastname": LABEL_LASTNAME,
            "participant_2_lastname": LABEL_LASTNAME,
            "participant_1_email": LABEL_EMAIL,
            "participant_2_email": LABEL_EMAIL,
            "participant_1_phone": LABEL_PHONE,
            "participant_2_phone": LABEL_PHONE,
            "allergies": LABEL_ALLERGIES,
            "like": LABEL_LIKE,
            "dislike": LABEL_DISLIKE,
        }

        help_texts = {
            "name": INFO_NAME,
            "doorbell": INFO_DOORBELL,
        }

        widgets = {
            "name": forms.TextInput(attrs={'class': 'form-control'}),
            "street": forms.TextInput(attrs={'class': 'form-control'}),
            "city": forms.TextInput(attrs={'class': 'form-control'}),
            "postal_code": forms.TextInput(attrs={'class': 'form-control'}),
            "doorbell": forms.TextInput(attrs={'class': 'form-control'}),
            "participant_1_firstname": forms.TextInput(
                attrs={'class': 'form-control'}),
            "participant_1_lastname": forms.TextInput(
                attrs={'class': 'form-control'}),
            "participant_1_email": forms.EmailInput(
                attrs={'class': 'form-control'}),
            "participant_1_phone": forms.TextInput(
                attrs={'class': 'form-control'}),
            "participant_2_firstname": forms.TextInput(
                attrs={'class': 'form-control'}),
            "participant_2_lastname": forms.TextInput(
                attrs={'class': 'form-control'}),
            "participant_2_email": forms.EmailInput(
                attrs={'class': 'form-control'}),
            "participant_2_phone": forms.TextInput(
                attrs={'class': 'form-control'}),
            "allergies": forms.Textarea(attrs={'class': 'form-control'}),
            "like": forms.CheckboxSelectMultiple(),
            "dislike": forms.CheckboxSelectMultiple(),
        }

    def clean(self):
        cleaned_data = super(RegistrationForm, self).clean()
        like = set(cleaned_data.get("like"))
        dislike = set(cleaned_data.get("dislike"))
        intersect = like & dislike
        if intersect:
            raise ValidationError(ERROR_PREFERENCES)


class CustomMailForm(forms.Form):
    subject = forms.CharField(label="Subject")
    body = forms.CharField(label="Body", widget=forms.Textarea)
