from django.conf import settings
from django.core.exceptions import ValidationError
import googlemaps
from pulp import LpBinary, LpMaximize, LpProblem,\
    LpVariable, value
from rudi.models import Course, Group


ERROR_MULTIPLE_EVENTS = "Not all groups belonged to the same event"
ERROR_MIN_TEAM_NOT_FULLFILLED = "There must be at least 9 teams to be assigned"
ERROR_NOT_DIVIDABLE_BY_THREE = "The number of teams is not dividable by 3"
DEFAULT_DISTANCE = 1200


class Coordinator():

    def __init__(self, teams):
        self.teams = teams

    def assign_to_groups(self, method="simple"):
        if method == "simple":
            self._load_data_simple()
        elif method == "distance":
            # TODO ensure that there is only one instance running
            # (e.g. celery lock)
            self._load_data_distance()
        else:
            raise ValidationError("unkown assignment method %s" % method)
        self.prob.solve()

    def get_groups(self):
        members = {}
        chefs = {}
        for c in self.COURSES:
            members[c] = {}
            chefs[c] = {}
            for g in self.groups:
                members[c][g] = []
                chefs[c][g] = None
                for t in self.teams:
                    if value(self.chef[c][t][g]) == 1:
                        chefs[c][g] = t
                    if value(self.assign[c][t][g]) == 1 and\
                            t != chefs[c][g]:
                        members[c][g].append(t)
        return (chefs, members)

    def create_group_entries(self):
        # delete old group assignments
        Group.objects.filter(event=self.event).delete()
        (chefs, members) = self.get_groups()
        counter = 0
        for c in self.COURSES:
            for g in self.groups:
                Group.objects.create(
                    course=c,
                    event=self.event,
                    chef=chefs[c][g],
                    member1=members[c][g][0],
                    member2=members[c][g][1],
                )
                counter += 1
        return counter

    def _load_data_simple(self):
        # There must be at least 9 teams to perform the assigment
        if len(self.teams) < 9:
            raise ValidationError(ERROR_MIN_TEAM_NOT_FULLFILLED)
        # The number of teams must be dividable by 3
        if len(self.teams) % 3:
            raise ValidationError(ERROR_NOT_DIVIDABLE_BY_THREE)
        self.COURSES = [
            Course.objects.get(name="a"),
            Course.objects.get(name="m"),
            Course.objects.get(name="d"),
        ]
        self.event = None
        self.groups = [g for g in range(len(self.teams) / 3)]
        self.happiness = {}
        self.distance = {}
        # Sets
        for t in self.teams:
            # check if all teams are from the same event
            if self.event:
                if self.event != t.event:
                    raise ValidationError(ERROR_MULTIPLE_EVENTS)
            else:
                self.event = t.event
            self.happiness[t] = {}
            for c in self.COURSES:
                self.happiness[t][c] = 0
            for l in t.like.all():
                self.happiness[t][l] = 1
            for d in t.dislike.all():
                self.happiness[t][d] = -1
        # binary Decision Variables
        self.assign = LpVariable.dicts(
            "Assign team t to group g for course ",
            (self.COURSES, self.teams, self.groups), 0, 1, LpBinary)
        self.chef = LpVariable.dicts(
            "Make team t chef of group g for course ",
            (self.COURSES, self.teams, self.groups), 0, 1, LpBinary)
        # add equations to model
        self._objective_simple()
        self._team_to_group_per_course()
        self._teams_in_group_per_course()
        self._teams_only_once_in_same_group()
        self._team_as_chef_per_course()
        self._teams_as_chef_in_group()
        self._teams_as_chef_once()
        self._teams_as_chef_only_in_group()

    def _load_data_distance(self):
        # There must be at least 9 teams to perform the assigment
        if len(self.teams) < 9:
            raise ValidationError(ERROR_MIN_TEAM_NOT_FULLFILLED)
        # The number of teams must be dividable by 3
        if len(self.teams) % 3:
            raise ValidationError(ERROR_NOT_DIVIDABLE_BY_THREE)
        self.COURSES_WITH_START = [
            "s",
            Course.objects.get(name="a"),
            Course.objects.get(name="m"),
            Course.objects.get(name="d"),
        ]
        self.COURSES = [
            Course.objects.get(name="a"),
            Course.objects.get(name="m"),
            Course.objects.get(name="d"),
        ]
        self.event = None
        self.groups = [g for g in range(len(self.teams) / 3)]
        self.happiness = {}
        self.distance = {}
        self.gmaps = googlemaps.Client(key=settings.GOOGLE_API_KEY)
        # Sets
        for t in self.teams:
            # check if all teams are from the same event
            if self.event:
                if self.event != t.event:
                    raise ValidationError(ERROR_MULTIPLE_EVENTS)
            else:
                self.event = t.event
            # Accept a longer walking time of up to ten minutes before
            # assigning less prefered courses
            self.happiness[t] = {}
            for c in self.COURSES:
                self.happiness[t][c] = 0
            for l in t.like.all():
                self.happiness[t][l] = 600
            for d in t.dislike.all():
                self.happiness[t][d] = -600
            self.distance[t] = {}
            for dt in self.teams:
                if dt is t:
                    self.distance[t][dt] = 0
                else:
                    # TODO mind max. request limit server not responding
                    # TODO save known distances to avoid unnecessary requests
                    try:
                        r = self.gmaps.distance_matrix(
                            origins="%s,%s,%s" % (
                                t.postal_code, t.city, t.street),
                            destinations="%s,%s,%s" % (
                                dt.postal_code, dt.city, dt.street),
                            mode="walking",
                        )
                    except googlemaps.exceptions.Timeout():
                        self.distance[t][dt] = DEFAULT_DISTANCE
                    else:
                        self.distance[t][dt] =\
                            r["rows"][0]["elements"][0]["duration"]["value"]\
                            if r else DEFAULT_DISTANCE
        # binary Decision Variables
        self.assign = LpVariable.dicts(
            "Assign team t to group g for course ",
            (self.COURSES, self.teams, self.groups), 0, 1, LpBinary)
        self.chef = LpVariable.dicts(
            "Make team t chef of group g for course ",
            (self.COURSES, self.teams, self.groups), 0, 1, LpBinary)
        self.arc = LpVariable.dicts(
            "The Route between team i and team j for team t in course c in group g",
            (self.COURSES, self.teams, self.teams, self.teams, self.groups), 0, 1, LpBinary)
        # add equations to model
        self._objective_distance()
        self._team_to_group_per_course()
        self._teams_in_group_per_course()
        self._teams_only_once_in_same_group()
        self._team_as_chef_per_course()
        self._teams_as_chef_in_group()
        self._teams_as_chef_once()
        self._teams_as_chef_only_in_group()
        self._routes_for_assigned_teams_only()
        self._start_from_home()
        self._routes_to_chef_only()
        self._start_from_previous_destination()

    def _objective_simple(self):
        """
        Optimization objective.

        Maximize the happiness of all teams.
        """
        self.prob = LpProblem("Team Assignment", LpMaximize)
        self.prob += sum(
            self.chef[c][t][g] * self.happiness[t][c]
            for c in self.COURSES for t in self.teams
            for g in self.groups
        )

    def _objective_distance(self):
        """
        Optimization objective.

        Maximize the happiness of all teams.
        """
        self.prob = LpProblem("Team Assignment", LpMaximize)
        self.prob += sum(
            self.chef[c][t][g] * self.happiness[t][c] -
            self.arc[c][i][j][t][g] * self.distance[i][j]
            for c in self.COURSES for t in self.teams
            for i in self.teams for j in self.teams
            for g in self.groups
        )

    def _routes_for_assigned_teams_only(self):
        """
        in each course each team can go only the route to a group if it is assigned to it
        """
        for c in range(1, len(self.COURSES)):
            for t in self.teams:
                for g in self.groups:
                    self.prob += sum(
                        [self.arc[self.COURSES[c]][i][j][t][g] for i in self.teams
                         for j in self.teams]) == self.assign[self.COURSES[c]][t][g]

    def _start_from_home(self):
        """
        teams start from their home location
        """
        for t in self.teams:
            for g in self.groups:
                self.prob += sum(
                    [self.arc[self.COURSES[0]][t][j][t][g] for j in self.teams])\
                             == self.assign[self.COURSES[0]][t][g]

    def _routes_to_chef_only(self):
        """
        Teams can only go to the chef of their group
        """
        for c in self.COURSES:
            for t in self.teams:
                for i in self.teams:
                    for j in self.teams:
                        for g in self.groups:
                            self.prob += self.arc[c][i][j][t][g]\
                             <= self.chef[c][j][g]

    def _start_from_previous_destination(self):
        """
        The starting point for a route is the destinatino of prev. course
        """
        for c in range(1, len(self.COURSES)):
            for t in self.teams:
                for i in self.teams:
                    self.prob +=\
                        sum([self.arc[self.COURSES[c]][i][j][t][g] for j in self.teams for g in self.groups if j is not i])\
                         == sum([self.arc[self.COURSES[c-1]][r][i][t][g] for r in self.teams for g in self.groups])


    def _team_to_group_per_course(self):
        """
        Assign each team to exactly one group per course.
        """
        for c in self.COURSES:
            for t in self.teams:
                self.prob += sum(
                    [self.assign[c][t][g] for g in self.groups])\
                    == 1

    def _teams_in_group_per_course(self):
        """
        Assign exactly 3 teams to a group per course.
        """
        for c in self.COURSES:
            for g in self.groups:
                self.prob += sum(
                    [self.assign[c][t][g] for t in self.teams])\
                    == 3

    def _teams_only_once_in_same_group(self):
        """
        Assign teams only once to be in the same group.

        In case they would be in the same group again for another course
        the sum of their assignments would be 4.
        """
        for c1 in range(len(self.COURSES)):
            for c2 in range(c1+1, len(self.COURSES)):
                for g1 in self.groups:
                    for g2 in self.groups:
                        for t1 in range(len(self.teams)):
                            for t2 in range(t1+1, len(self.teams)):
                                self.prob +=\
                                    self.assign[
                                        self.COURSES[c1]][
                                        self.teams[t1]][g1] +\
                                    self.assign[
                                        self.COURSES[c1]][
                                        self.teams[t2]][g1] +\
                                    self.assign[
                                        self.COURSES[c2]][
                                        self.teams[t1]][g2] +\
                                    self.assign[
                                        self.COURSES[c2]][
                                        self.teams[t2]][g2] <= 3

    def _team_as_chef_per_course(self):
        """
        There can only be one chef in one group per course.

        Not every team has to be chef in a course.
        """
        for c in self.COURSES:
            for t in self.teams:
                self.prob += sum(
                    [self.chef[c][t][g] for g in self.groups])\
                    <= 1

    def _teams_as_chef_in_group(self):
        """
        There is exactly one chef in one group per course.
        """
        for c in self.COURSES:
            for g in self.groups:
                self.prob += sum(
                    [self.chef[c][t][g] for t in self.teams])\
                    == 1

    def _teams_as_chef_once(self):
        """
        Set any team to be chef only once.
        """

        for c1 in range(len(self.COURSES)):
            for c2 in range(c1+1, len(self.COURSES)):
                for t in self.teams:
                    for g1 in self.groups:
                        for g2 in self.groups:
                            self.prob += self.chef[self.COURSES[c1]][t][g1] +\
                                self.chef[self.COURSES[c2]][t][g2] <= 1

    def _teams_as_chef_only_in_group(self):
        """
        Set a teams to be chef in a group only if it is that group.
        """

        for c in self.COURSES:
            for t in self.teams:
                for g in self.groups:
                    self.prob += self.chef[c][t][g] <= self.assign[c][t][g]
