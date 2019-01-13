from django import forms
import random

from . import mails
from .forms import CustomMailForm
from .models import Advisor, Event, Group, Team
from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls import path, reverse
#from rudi.lp_coordinator import Coordinator


MESSAGE_GROUPS_ASSIGNED = "%s teams have successfully assigned to groups"
ERROR_PREFERENCES = 'You cannot like and dislike the same course'
ERROR_EMAIL_NOT_CONFIRMED = 'You may not assign teams to groups that have' \
                            ' not confirmed their E-Mail address'


class CustomTeamAdminForm(forms.ModelForm):
    class Meta:
        model = Team
        exclude = ('code', "sent_assignment_mail",)
        widgets = {
            "like": forms.CheckboxSelectMultiple,
            "dislike": forms.CheckboxSelectMultiple,
        }

    def clean(self):
        cleaned_data = super(CustomTeamAdminForm, self).clean()
        like = set(cleaned_data.get("like"))
        dislike = set(cleaned_data.get("dislike"))
        intersect = like & dislike
        if intersect:
            raise ValidationError(ERROR_PREFERENCES)


class TeamAdmin(admin.ModelAdmin):
    form = CustomTeamAdminForm
    actions = ['assign_to_group_quick', 'assign_to_group_distance',
               "send_custom_mail"]
    list_display = (
        'event', 'name', 'participant_1_firstname', 'participant_1_lastname',
        'participant_2_firstname', 'participant_2_lastname', "language",
        "email_confirmed", "sent_mail")
    list_filter = ('event',)

    #def assign_to_group_quick(self, request, queryset):
    #    if queryset.filter(has_confirmed_email=False).exists():
    #        messages.error(request, ERROR_EMAIL_NOT_CONFIRMED)
    #        return
    #    try:
    #        coordinator = Coordinator(queryset)
    #    except ValidationError as e:
    #        messages.error(request, e.message)
    #    else:
    #        coordinator.assign_to_groups()
    #        entries = coordinator.create_group_entries()
    #        self.message_user(
    #            request, MESSAGE_GROUPS_ASSIGNED %
    #                     entries)

    #def assign_to_group_distance(self, request, queryset):
    #    if queryset.filter(has_confirmed_email=False).exists():
    #        messages.error(request, ERROR_EMAIL_NOT_CONFIRMED)
    #        return
    #    try:
    #        coordinator = Coordinator(queryset)
    #    except ValidationError as e:
    #        messages.error(request, e.message)
    #    else:
    #        coordinator.assign_to_groups(method="distance")
    #        entries = coordinator.create_group_entries()
    #        self.message_user(
    #            request, MESSAGE_GROUPS_ASSIGNED %
    #                     entries)

    def email_confirmed(self, obj):
        return bool(obj.has_confirmed_email)

    email_confirmed.short_description = "E-Mail confirmed?"
    email_confirmed.boolean = True

    def sent_mail(self, obj):
        return bool(obj.sent_assignment_mail)

    sent_mail.short_description = "Sent Assignment Mail?"
    sent_mail.boolean = True

    def send_custom_mail(self, request, queryset):
        form_id = str(random.randint(0, 2 ** 32 - 1))
        email_addresses = []
        advisor = None
        for team in queryset:
            if not advisor:
                advisor = team.event.advisor
            email_addresses.append(team.participant_1_email)
            if team.participant_2_email:
                email_addresses.append(team.participant_2_email)
        request.session["mailform_id"] = form_id
        request.session["mailform_advisor_" + form_id] = advisor.email
        request.session["mailform_addresses_" + form_id] = email_addresses
        referer = request.META["HTTP_REFERER"]
        if referer is None:
            referer = reverse("admin:index")
        request.session["mailform_referer_" + form_id] = referer
        form = CustomMailForm()
        return render(
            request,
            "admin/rudi/team/custom_mail.html",
            {
                "advisor": advisor,
                "email_addresses": email_addresses,
                "form": form,
            })

    def custom_mail_preview(self, request):
        if request.method == "POST":
            form = CustomMailForm(request.POST)
            form_id = request.session["mailform_id"]
            advisor = request.session["mailform_advisor_" + form_id]
            email_addresses = request.session["mailform_addresses_" + form_id]
            if form.is_valid():
                body = form.cleaned_data["body"]
                subject = form.cleaned_data["subject"]
                request.session["mailform_body_" + form_id] = body
                request.session["mailform_subject_" + form_id] = subject
                return render(
                    request,
                    "admin/rudi/team/custom_mail_preview.html",
                    {
                        "advisor": advisor,
                        "subject": subject,
                        "body": body,
                        "email_addresses": email_addresses,
                        "form": form,
                    })
            else:
                return render(
                    request,
                    "admin/rudi/team/custom_mail.html",
                    {
                        "advisor": advisor,
                        "email_addresses": email_addresses,
                        "form": form,
                    })
        else:
            return HttpResponseRedirect(reverse('admin:index'))

    def custom_mail_confirm(self, request):
        if request.method == "POST":
            form_id = request.session["mailform_id"]
            advisor = request.session["mailform_advisor_" + form_id]
            email_addresses = request.session[
                "mailform_addresses_" + form_id]
            body = request.session["mailform_body_" + form_id]
            subject = request.session["mailform_subject_" + form_id]
            sent_amount = mails.send_custom(
                advisor, email_addresses, subject, body)
            messages.add_message(
                request,
                messages.SUCCESS,
                "%s mails were sent successfully" % sent_amount)
            referer = request.session["mailform_referer_" + form_id]
            return HttpResponseRedirect(referer)
        else:
            return HttpResponseRedirect(reverse('admin:index'))

    def get_urls(self):
        urls = super(TeamAdmin, self).get_urls()
        custom_urls = [
            path("mail_preview/",
                 self.custom_mail_preview),
            path("mail_confirm/",
                 self.custom_mail_confirm),
        ]
        return custom_urls + urls


class GroupAdmin(admin.ModelAdmin):
    actions = ["send_assignment_mail"]
    list_display = ('event', 'course', 'chef_with_link', 'member1_with_link',
                    'member2_with_link',
                    "sent_mail")
    list_filter = ('event', 'course')

    def chef_with_link(self, obj):
        link = reverse("admin:rudi_team_change", args=[obj.chef.id])
        return "<a href='%s'>%s</a>" % (link, obj.chef)

    chef_with_link.allow_tags = True
    chef_with_link.short_description = "Chef"

    def member1_with_link(self, obj):
        link = reverse("admin:rudi_team_change", args=[obj.member1.id])
        return "<a href='%s'>%s</a>" % (link, obj.member1)

    member1_with_link.allow_tags = True
    member1_with_link.short_description = "Member1"

    def member2_with_link(self, obj):
        link = reverse("admin:rudi_team_change", args=[obj.member2.id])
        return "<a href='%s'>%s</a>" % (link, obj.member2)

    member2_with_link.allow_tags = True
    member2_with_link.short_description = "Member2"

    def sent_mail(self, obj):
        sent_assignment_mail = obj.chef.sent_assignment_mail and \
                               obj.member1.sent_assignment_mail and \
                               obj.member2.sent_assignment_mail
        return bool(sent_assignment_mail)

    sent_mail.short_description = "Sent Assignment Mail?"
    sent_mail.boolean = True

    def send_assignment_mail(self, request, queryset):
        (sent_amount, skipped) = mails.send_assignment(queryset)
        if skipped:
            messages.error(
                request,
                "skipped %s groups, because a mail was already"
                " sent to them" % skipped)
        if sent_amount:
            self.message_user(
                request,
                "%s mails were sent successfully to %s teams" %
                (sent_amount, len(queryset)))


admin.site.register(Advisor)
admin.site.register(Event)
admin.site.register(Team, TeamAdmin)
admin.site.register(Group, GroupAdmin)
