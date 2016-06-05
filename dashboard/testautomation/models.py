from __future__ import division, unicode_literals

from datetime import datetime

from dateutil.rrule import rrulestr
from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone
from django.utils.encoding import python_2_unicode_compatible


@python_2_unicode_compatible
class TestCase(models.Model):
    # Write
    title           = models.CharField(max_length=80, null=False)
    script          = models.FileField(upload_to='scripts')
    description     = models.TextField(null=True, blank=True)

    groups          = models.ManyToManyField('Group', blank=True)
    schedules       = models.ManyToManyField('Schedule', blank=True)

    # Read
    created         = models.DateTimeField(auto_now_add=True)
    created_by      = models.ForeignKey(User, related_name='test_case_create')
    last_updated    = models.DateTimeField('Last Updated', auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='test_case_update')

    # JIRA
    #jira_priority   =

    #jira_severity   =

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Group(models.Model):
    title           = models.CharField(max_length=80, null=False)
    description     = models.TextField(null=True, blank=True)
    test_cases      = models.ManyToManyField('TestCase', through=TestCase.groups.through, blank=True)
    schedules       = models.ManyToManyField('Schedule', blank=True)
    created         = models.DateTimeField('Created', auto_now_add=True)
    created_by      = models.ForeignKey(User, related_name='group_create')
    last_updated    = models.DateTimeField('Last updated', auto_now=True)
    last_updated_by = models.ForeignKey(User, related_name='group_update')

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Schedule(models.Model):
    # Write
    title = models.CharField(max_length=80, null=False)
    description = models.TextField(null=True, blank=True)
    test_cases = models.ManyToManyField('TestCase', through=TestCase.schedules.through, blank=True)
    groups = models.ManyToManyField('Group', through=Group.schedules.through, blank=True)

    start_time = models.DateTimeField('Start Time', null=True, blank=True)

    repeat = models.BooleanField('Repeat?')

    recurrence_rule = models.IntegerField(
        'Recurrence Pattern',
        choices=(
            (0, 'Repeat Daily'),
            (1, 'Repeat Weekly'),
            (2, 'Repeat Monthly')
        ),
        default=0,
    )

    range = models.IntegerField(
        'Range of Recurrence',
        choices=(
            (0, 'No End Date'),
            (2, 'End date')
        ),
        default=0,
    )

    end_by = models.DateTimeField('End By', null=True, blank=True)

    rrule_string = models.CharField(max_length=255, null=True, blank=True)

    def next_execution(self):
        if not self.activated:
            return None
        rule = rrulestr(self.rrule_string)
        utc_next_occurrence = rule.after(datetime.utcnow())
        if utc_next_occurrence:
            next_occurrence = utc_next_occurrence.replace(tzinfo=timezone.utc).astimezone(timezone.get_current_timezone())
            return next_occurrence
        return None

    next_execution.datetime = True
    next_execution.short_description = "Next Execution"

    # Read
    created_date = models.DateTimeField('Created', auto_now_add=True)
    last_updated = models.DateTimeField('Last updated', auto_now=True)
    passed_previous_execution = models.NullBooleanField(blank=True, null=True)
    last_execution = models.DateTimeField(blank=True, null=True)

    created_by = models.ForeignKey(User, related_name='schedule_create')
    last_updated_by = models.ForeignKey(User, related_name='schedule_update')

    activated = models.BooleanField('Activated?')

    def __str__(self):
        return self.title


@python_2_unicode_compatible
class Log(models.Model):
    # Test
    test_id         = models.IntegerField(editable=False)  # Integer and not ForeignKey because of cascading delete
    test            = models.CharField('Test Case', max_length=80)
    script_name     = models.CharField(max_length=200)
    result          = models.NullBooleanField()

    # Time
    start_time      = models.DateTimeField()
    end_time        = models.DateTimeField()
    total_duration  = models.FloatField(null=True)
    test_duration   = models.FloatField(null=True)

    # Environment
    test_machine_ip = models.CharField('Test Machine IP', max_length=30, null=True, blank=True)
    browser         = models.CharField(max_length=30, null=True, blank=True)
    browser_ver     = models.CharField(max_length=30, null=True, blank=True)
    platform        = models.CharField(max_length=30, null=True, blank=True)
    platform_ver    = models.CharField(max_length=30, null=True, blank=True)

    # Extra
    note            = models.TextField(blank=True, null=True)
    console_log     = models.TextField(blank=True, null=True)
    output          = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.test


@python_2_unicode_compatible
class TestMachine(models.Model):
    # BASIC
    hostname             = models.CharField(max_length=80)
    ip                   = models.CharField('IP', max_length=80, null=True, blank=True)
    url                  = models.CharField('URL', editable=False, max_length=80, null=True, blank=True)
    uuid                 = models.CharField('UUID', editable=False, max_length=80, null=True, blank=True)
    active               = models.BooleanField(editable=False)
    approved             = models.BooleanField()
    description = models.TextField(null=True, blank=True)

    # OPERATING SYSTEM
    operating_system     = models.CharField(max_length=30, null=True, blank=True, editable=False)
    operating_system_ver = models.CharField(max_length=30, null=True, blank=True, editable=False)

    # BROWSERS
    chrome               = models.CharField(max_length=255, null=True, blank=True, editable=False)
    firefox              = models.CharField(max_length=255, null=True, blank=True, editable=False)
    internet_explorer    = models.CharField(max_length=255, null=True, blank=True, editable=False)
    edge                 = models.CharField(max_length=255, null=True, blank=True, editable=False)

    def __str__(self):
        return self.hostname
