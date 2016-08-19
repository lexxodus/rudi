from __future__ import unicode_literals
from django.core.mail import send_mail, send_mass_mail
from django.core.urlresolvers import reverse
from django.db.models import Q
from django.template import Context, loader
from django.utils.translation import override
import email
from rudi.models import Group
import socket

SUBJECT_CODE = "Anmeldung zum %s %s"
SUBJECT_CODE = "%s %s - Teamzuweisung"


def send_single(context, text_template, subject, sender, recipients):
    text = text_template.render(context).encode("utf-8")

    # force 7bit/8bit content-transfer-encoding for text instead of base64
    # this helps to avoid getting caught by spam filters
    email.charset.add_charset("utf-8", email.charset.SHORTEST, None, None)

    return send_mail(
        subject=subject.encode("utf-8"),
        message=text,
        from_email=sender,
        recipient_list=recipients,
    )


def send_code(request, team):
    text_template = loader.get_template(
        "rudi/mails/code.txt")

    context = Context({
        "team": team,
        "link": request.build_absolute_uri(reverse(
            "rudi:confirm",
            args=(
                team.code,
            ),
        )),
    })
    subject = SUBJECT_CODE % (team.event.name, team.event.semester)
    if team.participant_2_email:
        recipients = [
            team.participant_1_email,
            team.participant_2_email
        ]
    else:
        recipients = [team.participant_1_email]
    with override(team.language):
        send_single(
            context,
            text_template,
            subject,
            team.event.advisor.email,
            recipients,
        )


def send_assignment(groups):
    sent = 0
    skipped = 0
    for group in groups:
        if not group.chef.sent_assignment_mail:
            sent += _send_assignment_per_course(group)
            group.chef.sent_assignment_mail = True
            group.chef.save()
        else:
            skipped += 1
    return (sent, skipped)

def _send_assignment_per_course(group):
    if group.course.name == "a":
        text_template = loader.get_template(
            "rudi/mails/assignment_appetizer.txt")
        chef_main_course = Group.objects.get(
            Q(member1=group.chef) | Q(member2=group.chef),
            event=group.event,
            course__name="m",
        )
        chef_dessert = Group.objects.get(
            Q(member1=group.chef) | Q(member2=group.chef),
            event=group.event,
            course__name="d",
        )
        context = Context({
            "chef": group.chef,
            "member1": group.member1,
            "member2": group.member2,
            "chef_main_course": chef_main_course.chef,
            "chef_dessert": chef_dessert.chef,
        })
    elif group.course.name == "m":
        text_template = loader.get_template(
            "rudi/mails/assignment_main_course.txt")
        chef_appetizer = Group.objects.get(
            Q(member1=group.chef) | Q(member2=group.chef),
            event=group.event,
            course__name="a",
        )
        chef_dessert = Group.objects.get(
            Q(member1=group.chef) | Q(member2=group.chef),
            event=group.event,
            course__name="d",
        )
        context = Context({
            "chef": group.chef,
            "member1": group.member1,
            "member2": group.member2,
            "chef_appetizer": chef_appetizer.chef,
            "chef_dessert": chef_dessert.chef,
        })
    elif group.course.name == "d":
        text_template = loader.get_template(
            "rudi/mails/assignment_dessert.txt")
        chef_appetizer = Group.objects.get(
            Q(member1=group.chef) | Q(member2=group.chef),
            event=group.event,
            course__name="a",
        )
        chef_main_course = Group.objects.get(
            Q(member1=group.chef) | Q(member2=group.chef),
            event=group.event,
            course__name="m",
        )
        context = Context({
            "chef": group.chef,
            "member1": group.member1,
            "member2": group.member2,
            "chef_appetizer": chef_appetizer.chef,
            "chef_main_course": chef_main_course.chef,
        })
    subject = SUBJECT_CODE % (group.event.name, group.event.semester)
    if group.chef.participant_2_email:
        recipients = [
            group.chef.participant_1_email,
            group.chef.participant_2_email
        ]
    else:
        recipients = [group.chef.participant_1_email]
    with override(group.chef.language):
        return send_single(
            context,
            text_template,
            subject,
            group.event.advisor.email,
            recipients,
        )


def send_custom(sender, recipients, subject, body):
    datalist = []
    for recipient in recipients:
        datalist.append((subject, body, sender, [recipient]))

    # force 7bit/8bit content-transfer-encoding for text instead of base64
    # this helps to avoid getting caught by spam filters
    email.charset.add_charset("utf-8", email.charset.SHORTEST, None, None)

    sent_amount = send_mass_mail(tuple(datalist))

    # Send confirmation to advisor
    advisor_body = "This is a confirmation message. The users"
    addresses = "\n - ".join(recipients)
    advisor_body += addresses + "were sent the following message:\n\n" + body
    send_mail(
        "Confirmation: " + subject,
        advisor_body,
        "rudi@%s" % socket.gethostname(),
        [sender]
    )

    return sent_amount
