# -*- coding: UTF-8 -*-
from __future__ import unicode_literals
import base58
from django.core.exceptions import FieldError, ValidationError
from django.db import models
from django.template import Context, Template
from django.utils.translation import ugettext_lazy as _
from hashlib import sha256
import random
import time

ERROR_EMAIL_DUPLICATE = _("Diese E-Mail Adresse darf nur einmal angegeben "
                          "werden.")
ERROR_EMAIL_EXISTING = _("Diese E-Mail Adresse wurde bereits von einem anderem"
                         " Team angemeldet.")
ERROR_NAME = _("Dieser Teamname existiert bereits.")
ERROR_PHONE = _('Bitte gib eine valide Telefonnummer an z.B. '
                '555 123321 or 0555-555-5-555')


class Advisor(models.Model):
    name = models.CharField(max_length=50)
    phone = models.CharField(max_length=50)
    email = models.EmailField()

    def __unicode__(self):
        return "%s" % self.name


class Event(models.Model):
    advisor = models.ForeignKey(Advisor)
    name = models.CharField(max_length=100)
    semester = models.CharField(
        max_length=50,
    )
    description_de = models.TextField(max_length=1000)
    description_en = models.TextField(max_length=1000)
    date = models.DateField()
    end_registration = models.DateField()
    appetizer_time = models.DateTimeField()
    main_course_time = models.DateTimeField()
    dessert_time = models.DateTimeField()
    afterparty_time = models.DateTimeField()
    afterparty_location = models.CharField(max_length=70)
    active = models.BooleanField(default=False)

    def clean(self):
        if self.active:
            try:
                # Raises an exception when there is no event set to active
                active_event = Event.objects.get(active=True)
            except:
                pass
            else:
                # Don't raise an Error if the active module is the current
                if active_event != self:
                    raise ValidationError({
                        'active':
                        'The dinner of %s is already set to active!\
                         Deactive this event first to activate this one!'
                            % active_event.semester})

    def get_dynamic_desc(self, language):
        if language == "en":
            template = Template(self.description_en)
        else:
            template = Template(self.description_de)
        context = Context({
            "advisor": self.advisor,
            "afterparty_location": self.afterparty_time,
            "afterparty_time": self.afterparty_time,
            "appetizer_time": self.appetizer_time,
            "event_date": self.date,
            "dessert_time": self.dessert_time,
            "end_registration": self.end_registration,
            "event_name": self.name,
            "event_semester": self.semester,
            "main_course_time": self.main_course_time,
        })
        dyn_desc = template.render(context)
        return dyn_desc

    def __unicode__(self):
        return "%s" % self.semester


class Course(models.Model):
    CHOICES_NAME = (
        ("a", _("Vorspeise")),
        ("m", _("Hauptgang")),
        ("d", _("Nachspeise")),
    )
    name = models.CharField(
        max_length=1,
        choices=CHOICES_NAME,
    )

    def __unicode__(self):
        return "%s" % self.get_name_display()


class Team(models.Model):
    event = models.ForeignKey(Event)
    name = models.CharField(max_length=100, verbose_name="Team Name")
    street = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    postal_code = models.CharField(max_length=10)
    doorbell = models.CharField(max_length=200, blank=True, null=True)
    participant_1_firstname = models.CharField(
        max_length=50)
    participant_1_lastname = models.CharField(
        max_length=50)
    participant_1_email = models.EmailField()
    participant_1_phone = models.CharField(max_length=50)
    participant_2_firstname = models.CharField(
        max_length=50)
    participant_2_lastname = models.CharField(
        max_length=50)
    participant_2_email = models.EmailField(
        blank=True, null=True)
    participant_2_phone = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    allergies = models.TextField(
        max_length=500,
        null=True,
        blank=True)
    like = models.ManyToManyField(
        Course,
        blank=True,
        related_name="like"
    )
    dislike = models.ManyToManyField(
        Course,
        blank=True,
        related_name="dislike"
    )
    code = models.CharField(
        max_length=64, editable=False, unique=True
    )
    language = models.CharField(max_length=2, null=True, blank=True)
    has_confirmed_email = models.BooleanField(default=False)
    sent_assignment_mail = models.BooleanField(default=False)

    def clean(self):

        if self.name and self.event:
            try:
                team = Team.objects.filter(event=self.event).get(
                    name=self.name)
            except:
                pass
            else:
                if team != self:
                    raise ValidationError(
                        {"name": ERROR_NAME})

        if self.participant_1_phone:
            if ModelHelper.is_phone(self.participant_1_phone):
                self.participant_1_phone = ModelHelper.clean_phone(
                        self.participant_1_phone)
            else:
                raise ValidationError(
                    {"participant_1_phone": ERROR_PHONE}
                )

        if self.participant_2_phone:
            if ModelHelper.is_phone(self.participant_2_phone):
                self.participant_2_phone = ModelHelper.clean_phone(
                        self.participant_2_phone)
            else:
                raise ValidationError(
                    ERROR_EMAIL_DUPLICATE
                )

        if self.participant_1_email and self.event:
            teams = []
            try:
                teams.append(Team.objects.filter(event=self.event).get(
                    participant_1_email=self.participant_1_email))
            except Team.DoesNotExist:
                pass
            try:
                teams.append(Team.objects.filter(event=self.event).get(
                    participant_2_email=self.participant_1_email))
            except Team.DoesNotExist:
                pass
            if teams and self not in teams:
                raise ValidationError(
                    {"participant_1_email": ERROR_EMAIL_EXISTING})

        if self.participant_2_email and self.event:
            teams = []
            try:
                teams.append(Team.objects.filter(event=self.event).get(
                    participant_1_email=self.participant_2_email))
            except Team.DoesNotExist:
                pass
            try:
                teams.append(Team.objects.filter(event=self.event).get(
                    participant_2_email=self.participant_2_email))
            except Team.DoesNotExist:
                pass
            if teams and self not in teams:
                raise ValidationError(
                    {"participant_2_email": ERROR_EMAIL_EXISTING})

        if self.participant_1_email and self.participant_2_email:
            if self.participant_1_email == self.participant_2_email:
                raise ValidationError(
                    ERROR_EMAIL_DUPLICATE
                )

        if not self.code and self.event:
            self.create_code()

    def create_code(self):
        if self.code:
            raise FieldError
        hash_input = (
            "fim_rudi" + self.participant_1_email +
            str(time.clock()) +
            str(self.event) +
            str(random.random()))
        digest = sha256(hash_input).digest()
        # if code already exists create another
        new_code = base58.b58encode(digest)
        if Team.objects.filter(code=new_code).exists():
            return self.create_code()
        self.code = new_code

    def __unicode__(self):
        return "%s" % self.name


class Group(models.Model):
    course = models.ForeignKey(Course)
    event = models.ForeignKey(Event)
    chef = models.ForeignKey(Team, related_name="chef")
    member1 = models.ForeignKey(Team, related_name="member1")
    member2 = models.ForeignKey(Team, related_name="member2")

    def __unicode__(self):
        return "course:%s, chef:%s, member1:%s, member2:%s" %\
                (self.course, self.chef, self.member1, self.member2)


class ModelHelper():
    @staticmethod
    def clean_phone(number):
        return number.replace(" ", "").replace("/", "")\
            .replace("-", "")

    @staticmethod
    def is_phone(number):
        phone = ModelHelper.clean_phone(number)
        try:
            int(phone)
        except ValueError:
            return False
        return True
