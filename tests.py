# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from datetime import date
from django.contrib.admin.sites import AdminSite
from django.core import mail
from django.core.urlresolvers import reverse
from django.utils import timezone
from django.test import LiveServerTestCase, RequestFactory
import email
import imaplib
import re
from rudi import mails
from lp_coordinator import Coordinator
from rudi.models import Advisor, Event, Course, Team, Group

EMAIL_DOMAIN = "localhost"

# Create your tests here.
class RunningDinnerTestCase(LiveServerTestCase):
    fixtures = [
        'rudi/fixtures/rudi_courses.json',
    ]

    def setUp(self):
        appetizer_time = timezone.datetime(
            date.today().year,
            date.today().month,
            date.today().day,
            17,
        ),
        main_course_time = timezone.datetime(
            date.today().year,
            date.today().month,
            date.today().day,
            18,
            30,
        ),
        dessert_time = timezone.datetime(
            date.today().year,
            date.today().month,
            date.today().day,
            20,
            30,
        )
        afterparty_time = timezone.datetime(
            date.today().year,
            date.today().month,
            date.today().day,
            20,
            30,
        )
        self.appetizer = Course.objects.get(name="a")
        self.main_menu = Course.objects.get(name="m")
        self.dessert = Course.objects.get(name="d")
        advisor = Advisor(
            name="TestAdvisorName",
            phone="0123000001",
            email="testuser1@%s" % EMAIL_DOMAIN
        )
        advisor.full_clean()
        advisor.save()
        self.event = Event(
            advisor=advisor,
            name="TestEventName",
            semester="TestEventSemester",
            description_de="TestEventDescriptionDE",
            description_en="TestEventDescriptionEN",
            date="%s" % (date.today() + timezone.timedelta(weeks=4)),
            end_registration="%s" % (date.today() + timezone.timedelta(weeks=3)),
            appetizer_time="%s" % appetizer_time,
            main_course_time="%s" % main_course_time,
            dessert_time="%s" % dessert_time,
            afterparty_time="%s" % afterparty_time,
            afterparty_location="TestAfterpartyLocation",
            active=True,
        )
        self.event.full_clean()
        self.event.save()
        team1 = Team(
            event=self.event,
            name="TestTeam1Name",
            street="Mittelstraße 129",
            city="Mannheim",
            postal_code="68169",
            doorbell="TestTeam1Doorbell",
            participant_1_firstname="TestTeam1Participant1Firstname",
            participant_1_lastname="TestTeam1Participant1Lastname",
            participant_1_email="testuser2@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000002",
            participant_2_firstname="TestTeam1Participant2Firstname",
            participant_2_lastname="TestTeam1Participant2Lastname",
            participant_2_email="testuser3@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000003",
            allergies="TestTeam1Allergies",
            language="de",
        )
        team1.full_clean()
        team1.save()
        team1.like.add(self.appetizer)
        team2 = Team(
            event=self.event,
            name="TestTeam2Name",
            street="Am Meßplatz 1",
            city="Mannheim",
            postal_code="68169",
            doorbell="TestTeam2Doorbell",
            participant_1_firstname="TestTeam2Participant1Firstname",
            participant_1_lastname="TestTeam2Participant1Lastname",
            participant_1_email="testuser4@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000004",
            participant_2_firstname="TestTeam2Participant2Firstname",
            participant_2_lastname="TestTeam2Participant2Lastname",
            participant_2_email="testuser5@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000005",
            allergies="TestTeam2Allergies",
            language="de",
        )
        team2.full_clean()
        team2.save()
        team2.like.add(self.appetizer)
        team2.like.add(self.main_menu)
        team3 = Team(
            event=self.event,
            name="TestTeam3Name",
            street="Mozartstr. 9",
            city="Mannheim",
            postal_code="68161",
            doorbell="TestTeam3Doorbell",
            participant_1_firstname="TestTeam3Participant1Firstname",
            participant_1_lastname="TestTeam3Participant1Lastname",
            participant_1_email="testuser6@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000006",
            participant_2_firstname="TestTeam3Participant2Firstname",
            participant_2_lastname="TestTeam3Participant2Lastname",
            participant_2_email="testuser7@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000007",
            allergies="TestTeam3Allergies",
            language="de",
        )
        team3.full_clean()
        team3.save()
        team3.like.add(self.appetizer)
        team3.like.add(self.dessert)
        team4 = Team(
            event=self.event,
            name="TestTeam4Name",
            street="Böckstraße 16",
            city="Mannheim",
            postal_code="68159",
            doorbell="TestTeam4Doorbell",
            participant_1_firstname="TestTeam4Participant1Firstname",
            participant_1_lastname="TestTeam4Participant1Lastname",
            participant_1_email="testuser8@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000008",
            participant_2_firstname="TestTeam4Participant2Firstname",
            participant_2_lastname="TestTeam4Participant2Lastname",
            participant_2_email="testuser9@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000009",
            allergies="TestTeam4Allergies",
            language="de",
        )
        team4.full_clean()
        team4.save()
        team4.like.add(self.appetizer)
        team4.dislike.add(self.main_menu)
        team4.dislike.add(self.dessert)
        team5 = Team(
            event=self.event,
            name="TestTeam5Name",
            street="H7 7",
            city="Mannheim",
            postal_code="68161",
            doorbell="TestTeam5Doorbell",
            participant_1_firstname="TestTeam5Participant1Firstname",
            participant_1_lastname="TestTeam5Participant1Lastname",
            participant_1_email="testuser10@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000010",
            participant_2_firstname="TestTeam5Participant2Firstname",
            participant_2_lastname="TestTeam5Participant2Lastname",
            participant_2_email="testuser11@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000011",
            allergies="TestTeam5Allergies",
            language="de",
        )
        team5.full_clean()
        team5.save()
        team5.like.add(self.main_menu)
        team6 = Team(
            event=self.event,
            name="TestTeam6Name",
            street="T4 5",
            city="Mannheim",
            postal_code="68161",
            doorbell="TestTeam6Doorbell",
            participant_1_firstname="TestTeam6Participant1Firstname",
            participant_1_lastname="TestTeam6Participant1Lastname",
            participant_1_email="testuser12@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000012",
            participant_2_firstname="TestTeam6Participant2Firstname",
            participant_2_lastname="TestTeam6Participant2Lastname",
            participant_2_email="testuser13@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000013",
            allergies="TestTeam6Allergies",
            language="de",
        )
        team6.full_clean()
        team6.save()
        team6.like.add(self.main_menu)
        team6.like.add(self.appetizer)
        team7 = Team(
            event=self.event,
            name="TestTeam7Name",
            street="B7 9",
            city="Mannheim",
            postal_code="68161",
            doorbell="TestTeam7Doorbell",
            participant_1_firstname="TestTeam7Participant1Firstname",
            participant_1_lastname="TestTeam7Participant1Lastname",
            participant_1_email="testuser14@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000014",
            participant_2_firstname="TestTeam7Participant2Firstname",
            participant_2_lastname="TestTeam7Participant2Lastname",
            participant_2_email="testuser15@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000015",
            allergies="TestTeam7Allergies",
            language="de",
        )
        team7.full_clean()
        team7.save()
        team7.like.add(self.main_menu)
        team7.like.add(self.dessert)
        team8 = Team(
            event=self.event,
            name="TestTeam8Name",
            street="N5 2",
            city="Mannheim",
            postal_code="68161",
            doorbell="TestTeam8Doorbell",
            participant_1_firstname="TestTeam8Participant1Firstname",
            participant_1_lastname="TestTeam8Participant1Lastname",
            participant_1_email="testuser16@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000016",
            participant_2_firstname="TestTeam8Participant2Firstname",
            participant_2_lastname="TestTeam8Participant2Lastname",
            participant_2_email="testuser17@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000017",
            allergies="TestTeam8Allergies",
            language="de",
        )
        team8.full_clean()
        team8.save()
        team8.like.add(self.main_menu)
        team8.dislike.add(self.appetizer)
        team8.dislike.add(self.dessert)
        team9 = Team(
            event=self.event,
            name="TestTeam9Name",
            street="Rathenaustraße 19",
            city="Mannheim",
            postal_code="68165",
            doorbell="TestTeam9Doorbell",
            participant_1_firstname="TestTeam9Participant1Firstname",
            participant_1_lastname="TestTeam9Participant1Lastname",
            participant_1_email="testuser18@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000018",
            participant_2_firstname="TestTeam9Participant2Firstname",
            participant_2_lastname="TestTeam9Participant2Lastname",
            participant_2_email="testuser19@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000019",
            allergies="TestTeam9Allergies",
            language="de",
        )
        team9.full_clean()
        team9.save()
        team9.like.add(self.dessert)
        team10 = Team(
            event=self.event,
            name="TestTeam10Name",
            street="Spinozastraße 11",
            city="Mannheim",
            postal_code="68165",
            doorbell="TestTeam10Doorbell",
            participant_1_firstname="TestTeam10Participant1Firstname",
            participant_1_lastname="TestTeam10Participant1Lastname",
            participant_1_email="testuser20@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000020",
            participant_2_firstname="TestTeam10Participant2Firstname",
            participant_2_lastname="TestTeam10Participant2Lastname",
            participant_2_email="testuser21@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000021",
            allergies="TestTeam10Allergies",
            language="de",
        )
        team10.full_clean()
        team10.save()
        team10.like.add(self.dessert)
        team10.like.add(self.appetizer)
        team11 = Team(
            event=self.event,
            name="TestTeam11Name",
            street="Augartenstr 95",
            city="Mannheim",
            postal_code="68169",
            doorbell="TestTeam11Doorbell",
            participant_1_firstname="TestTeam11Participant1Firstname",
            participant_1_lastname="TestTeam11Participant1Lastname",
            participant_1_email="testuser22@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000022",
            participant_2_firstname="TestTeam11Participant2Firstname",
            participant_2_lastname="TestTeam11Participant2Lastname",
            participant_2_email="testuser23@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000023",
            allergies="TestTeam11Allergies",
            language="de",
        )
        team11.full_clean()
        team11.save()
        team11.like.add(self.dessert)
        team11.like.add(self.main_menu)
        team12 = Team(
            event=self.event,
            name="TestTeam12Name",
            street="Traubenstraße 14",
            city="Mannheim",
            postal_code="68199",
            doorbell="TestTeam12Doorbell",
            participant_1_firstname="TestTeam12Participant1Firstname",
            participant_1_lastname="TestTeam12Participant1Lastname",
            participant_1_email="testuser24@%s" % EMAIL_DOMAIN,
            participant_1_phone="0123000024",
            participant_2_firstname="TestTeam12Participant2Firstname",
            participant_2_lastname="TestTeam12Participant2Lastname",
            participant_2_email="testuser25@%s" % EMAIL_DOMAIN,
            participant_2_phone="0123000025",
            allergies="TestTeam12Allergies",
            language="de",
        )
        team12.full_clean()
        team12.save()
        team12.like.add(self.dessert)
        team12.dislike.add(self.appetizer)
        team12.dislike.add(self.main_menu)
        self.factory = RequestFactory()


    def test_email_confirmation(self):
        REGEX = r"http.+"
        test_team_names = ["TestTeam%sName" % i for i in range(1,13)]
        teams = Team.objects.filter(name__in=test_team_names)
        for team in teams:
            mails.send_code(self.factory.get("/dinner"), team)
            self.assertFalse(team.has_confirmed_email)
        for m in mail.outbox:
            link = re.findall(REGEX, m.body)[0]
            self.assertTemplateUsed(self.client.get(link), "rudi/code_confirmed.html")
            self.assertTemplateUsed(self.client.get(link), "rudi/code_already_confirmed.html")
        teams = Team.objects.filter(name__in=test_team_names)
        for team in teams:
            self.assertTrue(team.has_confirmed_email)


    def test_group_assignment(self):
        test_team_names = ["TestTeam%sName" % i for i in range(1,13)]
        teams = Team.objects.filter(name__in=test_team_names)
        coordinator = Coordinator(teams)
        coordinator.assign_to_groups()
        coordinator.create_group_entries()
        groups = Group.objects.filter(event=self.event)
        test_pairs = []
        chefs_remaining = teams[:]
        appetizer_remaining = teams[:]
        main_menu_remaining = teams[:]
        dessert_remaining = teams[:]
        for g in groups:
            # every team has to te in every course
            if g.course == self.appetizer:
                appetizer_remaining.remove(g.chef)
                appetizer_remaining.remove(g.member1)
                appetizer_remaining.remove(g.member2)
            if g.course == self.main_menu:
                main_menu_remaining.remove(g.chef)
                main_menu_remaining.remove(g.member1)
                main_menu_remaining.remove(g.member2)
            if g.course == self.dessert:
                dessert_remaining.remove(g.chef)
                dessert_remaining.remove(g.member1)
                dessert_remaining.remove(g.member2)
            # every team has to be chef once
            chefs_remaining.remove(g.chef)
            # every team may only be in the same group with others once
            rel1 = set([g.chef, g.member1])
            rel2 = set([g.chef, g.member2])
            rel3 = set([g.member1, g.member2])
            self.assertNotIn(rel1, test_pairs)
            self.assertNotIn(rel2, test_pairs)
            self.assertNotIn(rel3, test_pairs)
            test_pairs.append(rel1)
            test_pairs.append(rel2)
            test_pairs.append(rel3)
        self.assertFalse(appetizer_remaining)
        self.assertFalse(main_menu_remaining)
        self.assertFalse(dessert_remaining)
        self.assertFalse(chefs_remaining)

    def test_email_group_assignment(self):
         test_team_names = ["TestTeam%sName" % i for i in range(1,13)]
         teams = Team.objects.filter(name__in=test_team_names)
         team = dict()
         for t in teams:
             team[t.name] = t
         coordinator = Coordinator(teams)
         coordinator.assign_to_groups()# method="distance")
         coordinator.create_group_entries()
         groups = Group.objects.filter(event=self.event)
         chefs_appetizer = []
         chefs_main_menu = []
         chefs_dessert = []
         m1_appetizer = []
         m1_main_menu = []
         m1_dessert = []
         m2_appetizer = []
         m2_main_menu = []
         m2_dessert = []
         for g in groups:
             if g.course == self.appetizer:
                chefs_appetizer.append(g.chef)
                m1_appetizer.append(g.member1)
                m2_appetizer.append(g.member2)
             elif g.course == self.main_menu:
                 chefs_main_menu.append(g.chef)
                 m1_main_menu.append(g.member1)
                 m2_main_menu.append(g.member2)
             elif g.course == self.dessert:
                 chefs_dessert.append(g.chef)
                 m1_dessert.append(g.member1)
                 m2_dessert.append(g.member2)
         print(chefs_appetizer)
         print(m1_appetizer)
         print(m2_appetizer)
         print(chefs_main_menu)
         print(m1_main_menu)
         print(m2_main_menu)
         print(chefs_dessert)
         print(m1_dessert)
         print(m2_dessert)
         self.assertIn(team["TestTeam1Name"], chefs_appetizer)
         try:
             self.assertIn(team["TestTeam2Name"], chefs_appetizer)
         except AssertionError:
             self.assertIn(team["TestTeam2Name"], chefs_main_menu)
         try:
             self.assertIn(team["TestTeam3Name"], chefs_appetizer)
         except AssertionError:
             self.assertIn(team["TestTeam3Name"], chefs_dessert)
         self.assertIn(team["TestTeam4Name"], chefs_appetizer)
         self.assertIn(team["TestTeam5Name"], chefs_main_menu)
         try:
             self.assertIn(team["TestTeam6Name"], chefs_main_menu)
         except AssertionError:
             self.assertIn(team["TestTeam6Name"], chefs_appetizer)
         try:
             self.assertIn(team["TestTeam7Name"], chefs_main_menu)
         except AssertionError:
             self.assertIn(team["TestTeam7Name"], chefs_dessert)
         self.assertIn(team["TestTeam8Name"], chefs_main_menu)
         self.assertIn(team["TestTeam9Name"], chefs_dessert)
         try:
             self.assertIn(team["TestTeam10Name"], chefs_dessert)
         except AssertionError:
             self.assertIn(team["TestTeam10Name"], chefs_appetizer)
         try:
             self.assertIn(team["TestTeam11Name"], chefs_dessert)
         except AssertionError:
             self.assertIn(team["TestTeam11Name"], chefs_main_menu)
         self.assertIn(team["TestTeam12Name"], chefs_dessert)
         # tmp
         mails.send_assignment(groups)
         for m in mail.outbox:
             print("------")
             print(m.body)
             print("------")


