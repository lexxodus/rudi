RuDi Group Assignment
=====================

This django application provides a web interface for the registration and automated assignment of teams for a three course dinner known as RuDi or Running Dinner™.
Teams are informed via e-mail about the locations they need to go.

It uses a linear solver for determining the optimal constalation of groups.
A simple assignment is possible for large numbers of teams that only optimizes the happiness of all teams by assigning them preferred courses.
For smaller groups a distance assingment is available that also considers the total distance teams have to walk from each course to the next. Therefore a google maps distance matrix api key is required (<https://developers.google.com/maps/documentation/distance-matrix/>).

# Installation

You can simply add the application to a django project (written for Django 1.8.11)running with python2.7.x.
Also the google maps distance matrix key has to be added to your projects config file:

`GOOGLE_API_KEY = "<your_api_key>"`

After migrating the apps database tables you have to load the dinners courses:

`./manage.py loaddata rudi/fixtures/running_dinner_courses.json`

Then you have to add the apps urls to your projects urls.py:

```python
url(
    r'^dinner/',
    include(
        'rudi.urls', namespace="rudi"
    ),
)
```

# Usage

## Administrative Backend

In order to enable the registration of teams a advisor and a event have to be created.
The advisor will be the displayed as the contact person. Note that the advisor's email address will put in the senders field of the automated emails. Therefore it has to part of a domain owned by your server.
Registration is automatically activated within the entered start and end date.
Once registration is completed you can select the teams you want to assign. Note that teams must have confirmed their email addresses and must be registered for the same event. You must at least select nine teams and the amount of teams you select must be divisable by three. With the simple assignment you can quickly assign teams meeting the constraints of a RuDi. In case you want reduce the distance teams have to walk between each courses you can use the distance assignment. Note that this can take a (very) long time depending on the amount of teams selected (tested with 16 teams ~12 minutes). Previous assignments will be deleted once a new assignment process is started.
Once the assignment is finished the resulting groups can be viewed in the `groups` table. There you can select to notify the selected participants via e-mail.

## Registration Form

With the above url setup the registration form is available at `yourhost.com/dinner/`. Once a team has registered it will receive a confirmation e-mail with a link to confirm its e-mail address. Only teams with confirmed e-mail addresses can be assigned to groups.

# Calculations

The file `rudi_solver.pdf` contains the mathematical equations used for this application. In order to improve the calculation time of distance assignment one would have to use heuristics. These mathematical equations should help one to identify optimizations.
