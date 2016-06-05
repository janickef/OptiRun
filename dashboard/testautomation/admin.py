import ConfigParser
import httplib
import json
import os
import socket
from datetime import datetime
from os import path

from django.contrib import admin
from django.contrib import messages
from django.contrib.admin import helpers
from django.contrib.admin.views.main import ChangeList
from django.core import serializers
from django.db import models
from django.db.models import Avg
from django.forms import TextInput, Textarea
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.utils import formats

from django.contrib.admin import SimpleListFilter
from django.utils import timezone

from .forms import TestCaseAdminForm, ScheduleAdminForm
from .models import TestCase, Group, Schedule, Log, TestMachine

browsers = ['chrome', 'edge', 'firefox', 'internet explorer']


def capability_version_display(attr, attr_ver):
    try:
        ret_str = '<i class="fa fa-%s"></i> %s' % (attr.replace(" ", "-").lower(), attr.replace("-", " ").title())
        if attr_ver:
            ret_str += ' %s' % attr_ver
        return ret_str
    except:
        return "-"


def capability_display(attr):
    try:
        return '<i class="fa fa-%s"></i> %s' % (attr.replace(" ", "-").lower(), attr.replace("-", " ").title())
    except:
        return "-"


def format_number(attr):
    try:
        return "{0:.2f}".format(round(attr, 2)) + "s"
    except:
        #return "-"
        return None


def get_result(attr):
    color_class = ""
    if attr:
        color_class = "result-display-passed"
        icon = "check-circle"
        msg = "Passed"
    elif attr is False:
        color_class = "result-display-failed"
        icon = "times-circle"
        msg = "Failed"
    else:
        msg = "Not Executed"
        icon = "exclamation-circle"
    return '<span class="result-display nowrap %s"><i class="fa fa-%s"></i> %s</span>' % (color_class, icon, msg)


def get_server_settings(port_name):
    config = ConfigParser.ConfigParser()

    config_path = path.abspath(path.join(path.dirname(__file__), '..', 'config.ini'))
    config.read(config_path)

    port = config.get('CONTROLLER', port_name)

    return int(port)


class TestCaseChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super(TestCaseChangeList, self).__init__(*args, **kwargs)
        self.title = 'Test Cases'


class TestCaseAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return TestCaseChangeList

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None,     {'fields': ['title', 'script', 'description']}),
            ('Groups', {'fields': ['groups']}),
        ]

        if obj is not None:
            fieldsets += [
                ('Previous Execution',     {'fields': ['prev_date_link', 'prev_res']}),
                ('Execution Summary',      {'fields': ['times_run', 'avg_dur_display', 'result_summary']}),
                ('Created',                {'fields': ['created', 'created_by']}),
                ('Last Updated',           {'fields': ['last_updated', 'last_updated_by_display']})
            ]
        return fieldsets

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '40'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    readonly_fields = (
        'created',
        'created_by',
        'last_updated',
        'last_updated_by_display',
        'times_run',
        'prev_date',
        'prev_res',
        'avg_dur_display',
        'result_summary',
        'prev_date_link',
    )

    form = TestCaseAdminForm

    list_display = (
        'title',
        'times_run',
        'result_summary',
        'avg_dur_display',
        'prev_date',
        'prev_res',
    )

    filter_horizontal = (
        'groups',
    )

    list_filter = [
        'groups',
        'created_by',
        'last_updated_by',
    ]

    search_fields = [
        'title'
    ]

    def last_updated_by_display(self, obj):
        return obj.last_updated_by
    last_updated_by_display.short_description = "Last Updated by"

    # Field methods for TestCaseAdmin
    def times_run(self, obj):
        return Log.objects.filter(test_id=obj.pk).exclude(result__isnull=True).count()
    # times_run.short_description = "Number of Times Executed"
    times_run.short_description = "Execution Count"

    def result_summary(self, obj):
        passed_count = Log.objects.filter(test_id=obj.pk, result=True).count()
        failed_count = Log.objects.filter(test_id=obj.pk, result=False).count()
        ne_count     = Log.objects.filter(test_id=obj.pk, result=None).count()
        return '<span class="result-dist">%d,%d,%d</span>' % (passed_count, failed_count, ne_count)
    result_summary.allow_tags = True

    def avg_dur_display(self, obj):
        avg_dur = self.avg_dur(obj)
        return format_number(avg_dur)
    avg_dur_display.short_description = "Average Duration"

    def avg_dur(self, obj):
        return Log.objects.filter(test_id=obj.pk).exclude(result__isnull=True).aggregate(Avg('test_duration'))['test_duration__avg']

    def prev_date(self, obj):
        try:
            prev = Log.objects.filter(test_id=obj.pk).exclude(result__isnull=True).order_by('-end_time').first()
            prev_time = prev.end_time.replace(tzinfo=timezone.utc).astimezone(timezone.get_current_timezone())
            return formats.date_format(prev_time, "DATETIME_FORMAT")
        except:
            return "-"
    prev_date.short_description = "Previous Execution"

    def prev_date_link(self, obj):
        try:
            prev = Log.objects.filter(test_id=obj.pk).exclude(result__isnull=True).order_by('-end_time').first()
            prev_time = prev.end_time.replace(tzinfo=timezone.utc).astimezone(timezone.get_current_timezone())
            formatted = formats.date_format(prev_time, "DATETIME_FORMAT")
            tag_wrap = '<a href="/admin/web_test_automation/log/%d/change/" target="_blank">%s</a>' % (prev.pk, formatted)
            return tag_wrap
        except:
            return "-"
    prev_date_link.allow_tags = True
    prev_date_link.short_description = "Previous Execution"

    def prev_res(self, obj):
        try:
            prev = Log.objects.filter(test_id=obj.pk).exclude(result__isnull=True).order_by('-end_time').first()
            return get_result(prev.result)
        except:
            return "-"
    prev_res.short_description = "Previous Result"
    prev_res.allow_tags = True

    def admin_action(self, request, queryset):
        if request.POST.get('post'):
            data = []
            for obj in queryset:
                pk = str(obj.pk)
                browsers = request.POST.getlist(pk + '_browsers') + request.POST.getlist(pk + '_browsers_any')
                platform = request.POST.getlist(pk + '_platform')[0]

                for browser in browsers:
                    data.append({
                        'avg_duration': self.avg_dur(obj),
                        'browser':      browser,
                        'pk':           obj.pk,
                        'platform':     platform,
                        'script':       str(obj.script),
                        'title':        obj.title,
                    })

            port = get_server_settings('request_port')
            json_data = json.dumps(data)
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((socket.gethostname(), port))
                s.send(json_data)
                s.close()
                executions = len(queryset)
                if executions == 1:
                    message_part = "1 test case was"
                else:
                    message_part = "%s test cases were" % executions
                self.message_user(request, "%s sent to server for execution." % message_part)
            except:
                print "SOMETHING WENT WRONG"
                self.message_user(
                    request,
                    "Selected test cases were not executed. Contact with server could not be established.",
                    level=messages.ERROR
                )

        else:
            context = {
                'title': ("Test Environment"),
                'queryset': queryset,
                'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
            }
            return TemplateResponse(request, '../templates/admin/intermediate.html',
                context, current_app=self.admin_site.name)

    admin_action.short_description = 'Execute Now'

    """
    def execute_now(self, request, queryset):
        response = HttpResponse(content_type="application/json")
        serializers.serialize("json", queryset, stream=response)

        data = []

        for obj in queryset:
            data.append({
                'avg_duration': self.avg_dur(obj),
                'browser':      'firefox',
                'pk':           obj.pk,
                'platform':     'any',
                'script':       str(obj.script),
                'title':        obj.title,
            })

        json_data = json.dumps(data)

        #hostname, port = get_server_settings()
        port = get_server_settings('request_port')

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((socket.gethostname(), port))
            s.send(json_data)
            s.close()

            executions = len(queryset)
            if executions == 1:
                message_bit = "1 test case was"
            else:
                message_bit = "%s test cases were" % executions
            self.message_user(
                request,
                "%s sent to server for execution." % message_bit
            )
        except:
            self.message_user(
                request,
                "Selected test cases were not executed. Contact with server could not be established.",
                level=messages.ERROR
            )
    """

    # actions = [execute_now, admin_action]
    actions = [admin_action]

    # On save method for TestCaseAdmin
    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        obj.save()

    class Media:
        css = {
             'all': ('admin/css/widgets.css',)
        }

        js = (
            'http://code.jquery.com/jquery-2.2.1.min.js',
            'http://canvasjs.com/assets/script/jquery.canvasjs.min.js',
            'http://omnipotent.net/jquery.sparkline/2.1.2/jquery.sparkline.js',
            'js/test_case_admin.js',
        )

admin.site.register(TestCase, TestCaseAdmin)


class GroupChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super(GroupChangeList, self).__init__(*args, **kwargs)
        self.title = 'Groups'


class GroupAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return GroupChangeList

    formfield_overrides = {
        models.CharField: {'widget': TextInput(attrs={'size': '40'})},
        models.TextField: {'widget': Textarea(attrs={'rows': 4, 'cols': 40})},
    }

    fieldsets = [
        (None,          {'fields': ['title', 'description']}),
        ('Test Cases',  {'fields': ['test_cases']}),
    ]

    list_display = (
        'title',
        'created',
        'created_by',
        'last_updated',
        'last_updated_by',
    )

    filter_horizontal = ('test_cases',)

    list_filter = [
        'created_by',
        'last_updated_by',
    ]

    search_fields = [
        'title',
        'created_by',
        'last_updated_by',
        'description',
    ]

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.created_by = request.user
        obj.last_updated_by = request.user
        obj.save()

admin.site.register(Group, GroupAdmin)


class ScheduleChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super(ScheduleChangeList, self).__init__(*args, **kwargs)
        self.title = 'Schedules'


class ScheduleAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return ScheduleChangeList

    form = ScheduleAdminForm

    fieldsets = [
        (None,          {'fields': ['title', 'start_time', 'activated']}),
        ('Recurrence',  {'fields': ['repeat', 'recurrence_rule', 'range', 'end_by']}),
        ('Groups',      {'fields': ['groups']}),
        ('Test Cases',  {'fields': ['test_cases']}),
    ]

    list_display = ('title', 'activated', 'next_execution', 'recurrence_rule_display')
    filter_horizontal = ('test_cases', 'groups')
    radio_fields = {'recurrence_rule': admin.VERTICAL, 'range': admin.VERTICAL}

    list_filter = ['activated', 'created_by', 'last_updated_by']
    search_fields = ['title', 'created_by', 'last_updated_by']

    def recurrence_rule_display(self, obj):
        if obj.repeat and (obj.range == 0 or obj.end_by >= datetime.utcnow()):
            if obj.recurrence_rule == 0:
                return 'Daily'
            elif obj.recurrence_rule == 1:
                return 'Weekly'
            return 'Monthly'
        return '-'

    recurrence_rule_display.short_description = "Recurrence"

    def activate(self, request, queryset):
        changed_count = 0
        unchanged_count = 0
        data = []

        for obj in queryset:
            if not obj.activated:
                obj.activated = True
                changed_count += 1
                obj.save()

                data.append({
                    'pk'          : obj.pk,
                    'rrule_string': obj.rrule_string,
                    'activated'   : obj.activated
                })
            else:
                unchanged_count += 1
        if changed_count:
            if changed_count == 1:
                message_bit = "1 selected 'Schedule' item was "
            else:
                message_bit = "%d selected 'Schedule' items were " % changed_count
            self.message_user(request, "%s successfully activated." % message_bit)

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((socket.gethostname(), get_server_settings('schedule_port')))
                s.send(json.dumps(data))
                s.close()
            except:
                self.message_user(request, "Could not establish contact with test server", level=messages.ERROR)

        if unchanged_count:
            if unchanged_count == 1:
                message_bit = "1 selected 'Schedule' item was "
            else:
                message_bit = "%d selected 'Schedule' items were " % unchanged_count
            self.message_user(request, "%s already activated." % message_bit, level=messages.WARNING)

    def deactivate(self, request, queryset):
        changed_count = 0
        unchanged_count = 0
        data = []

        for obj in queryset:
            if obj.activated:
                obj.activated = False
                changed_count += 1
                obj.save()

                data.append({
                    'pk'          : obj.pk,
                    'rrule_string': obj.rrule_string,
                    'activated'   : obj.activated
                })
            else:
                unchanged_count += 1
        if changed_count:
            if changed_count == 1:
                message_bit = "1 selected 'Schedule' item was "
            else:
                message_bit = "%d selected 'Schedule' items were " % changed_count
            self.message_user(request, "%s successfully deactivated." % message_bit)

            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect((socket.gethostname(), get_server_settings('schedule_port')))
                s.send(json.dumps(data))
                s.close()
            except:
                self.message_user(request, "Could not establish contact with test server", level=messages.ERROR)
        if unchanged_count:
            if unchanged_count == 1:
                message_bit = "1 selected 'Schedule' item was "
            else:
                message_bit = "%d selected 'Schedule' items were " % unchanged_count
            self.message_user(request, "%s already deactivated." % message_bit, level=messages.WARNING)

    actions = [activate, deactivate]

    class Media:
        js = ('static/schedule_admin.js', 'schedule_admin.js')
        css = {
            'all': ('dynamic.css',)
        }

    def delete_model(self, request, obj):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((socket.gethostname(), get_server_settings('schedule_port')))
            s.send(json.dumps([obj.pk]))
            s.close()
        except:
            pass
    #def delete_selected

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.created_by = request.user
        obj.last_updated_by = request.user

        utc_diff = datetime.now() - datetime.utcnow()
        start_time = (obj.start_time-utc_diff).strftime("%Y%m%dT%H%M%S")
        rrule_string = "DTSTART:" + start_time + "\n"

        if obj.range == 1:
            end_time = obj.end_by.strftime("%Y%m%dT%H%M%S")
            rrule_string = "DTEND:" + end_time + "\n"

        rrule_string += "RRULE:"
        if obj.recurrence_rule == 0:
            pattern = "DAILY"
        elif obj.recurrence_rule == 1:
            pattern = "WEEKLY"
        else:
            pattern = "MONTHLY"
        rrule_string += "FREQ=" + pattern
        if not obj.repeat:
            rrule_string += ";COUNT=1"
            obj.end_by = None

        obj.rrule_string = rrule_string
        obj.save()

        data = [{
            'pk': obj.pk,
            'rrule_string': obj.rrule_string,
            'activated': obj.activated
        }]

        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.connect((socket.gethostname(), get_server_settings('schedule_port')))
            s.send(json.dumps(data))
            s.close()
        except:
            pass

admin.site.register(Schedule, ScheduleAdmin)


def get_jira_settings():
    """
    This method retrieves the URL of the Jira server, the username and the password from the configuration file.
    """

    config = ConfigParser.ConfigParser()
    config_path = os.path.abspath(os.path.join(path.dirname(__file__), '..', 'config.ini'))
    config.read(config_path)

    server = config.get('JIRA', 'server')
    username = config.get('JIRA', 'username')
    password = config.get('JIRA', 'password')
    project_key = config.get('JIRA', 'project_key')

    return server, username, password, project_key


jira_server, username, password, project_key = get_jira_settings()

jira_options = {
    'server':          jira_server,
    'verify':          False,
    'get_server_info': False
}


def check_access():
    try:
        httplib.HTTPConnection(jira_server.split("/")[-1], timeout=1).request("HEAD", "/")
        return True
    except:
        return False


def initiate_jira():
    from jira import JIRA

    return JIRA(
        options=jira_options,
        basic_auth=(username, password)
    )


def initiate():
    if check_access():
        return initiate_jira()
    return False


def get_description(obj):
    msg = '|*Test*|#%s: %s\n' % (str(obj.test_id), obj.test)
    msg += '|*Machine*|%s\n' % obj.test_machine_ip
    msg += '|*Browser*| %s ' % obj.browser.capitalize()
    if obj.browser_ver:
        msg += obj.browser_ver
    msg += '|\n'
    msg += '|*Operating System*| %s ' % obj.platform.capitalize()
    if obj.platform_ver:
        msg += obj.platform_ver
    msg += '|\n'
    if obj.note:
        msg += '|*Note*|%s|\n' % obj.note
    if obj.console_log:
        msg += '*Console Log:*\n{noformat}%s{noformat}\n' % obj.console_log
    if obj.output:
        msg += '*Output:*\n{noformat}%s{noformat}\n' % obj.output
    msg += '*/OptiRun*'
    return msg


def search(jira_instance, obj):
    """
    This method uses the JIRA REST API to search for issues that matches the search string that includes the ID and the
    title of the test, and returns a list of any matching results.
    """

    try:
        return jira_instance.search_issues(
            'project=%s '
            'AND reporter = currentUser() '
            'AND status != Closed '
            'AND type = Bug '
            'AND summary ~ "OptiRun: %s (%s) FAILED" '
            % (project_key, obj.test, str(obj.test_id))
        )
    except:
        return False


def create(jira_instance, obj):
    """
    This method uses the JIRA REST API to create a new issue.
    """

    try:
        jira_instance.create_issue(
            project=project_key,
            summary='OptiRun: %s (%s) FAILED' % (obj.test, str(obj.test_id)),
            description='*_Produced %s._*\n\n' % obj.end_time.strftime("%d.%m.%Y %H:%M") + get_description(obj),
            issuetype={'name': 'Bug'},
            components=[{'name': 'web'}],
            labels=[{'name': 'optirun'}]
        )
        return True
    except:
        return False


def comment(jira_instance, issue, obj):
    """
    This method uses the JIRA REST API to search for issues that matches the search string that includes the ID and the
    title of the test, and returns a list of any matching results.
    """

    try:
        msg = '*_Reproduced %s._*\n\n' % obj.end_time.strftime("%d.%m.%Y %H:%M")
        msg += get_description(obj)
        jira_instance.add_comment(issue.id, msg)
        return True
    except:
        return False


def report(obj):
    """
    This method uses the search method to find out if there are any non-closed issues regarding the same failed
    test. A comment saying that the problem has been reproduced is posted on any existing issues. If the search does
    not return any issues, a new issue is created.
    """

    jira_instance = initiate()
    if jira_instance:
        search_res = search(jira_instance, obj)
        if search_res:
            for issue in search_res:
                if not comment(jira_instance, issue, obj):
                    return create(jira_instance, obj)
            return True
        else:
            return create(jira_instance, obj)
    else:
        return False


def get_issues(obj):
    """
    This method uses the search method to find any existing non-closed issues regarding a specific test, and returns
    a dictionary of relevant information about them.
    """

    jira_instance = initiate()
    if jira_instance:
        try:
            return [{'key': item.key, 'url': '%s/browse/%s' % (jira_server, item.key)} for item in search(jira_instance, obj)]
            # return [{'key': item.key, 'url': '%s/browse/%s' % (jira_server, item.key)} for item in search(jira_instance, obj)]
            # return [{'key': "%s (%s)" % (item.key, item.status), 'url': '%s/browse/%s' % (jira_server, item.key)} for item in search(jira_instance, obj)]
            # return [{'key': item.key + item.fields.status, 'url': '%s/browse/%s' % (jira_server, item.key)} for item in search(jira_instance, obj)]
        except:
            return False
    else:
        return False


class LogResultFilter(SimpleListFilter):
    title = 'Result'
    parameter_name = 'result'

    def lookups(self, request, model_admin):
        return (
            ('PASSED', ('Passed')),
            ('FAILED', ('Failed')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'PASSED':
            return queryset.filter(result=True)
        elif self.value() == 'FAILED':
            return queryset.filter(result=False)


class LogExecutedFilter(SimpleListFilter):
    title = 'Executed?'
    parameter_name = 'executed'

    def lookups(self, request, model_admin):
        return (
            ('EXECUTED', 'Executed'),
            ('NOT EXECUTED', 'Not Executed'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'EXECUTED':
            return queryset.filter(result__isnull=False)
        elif self.value() == 'NOT EXECUTED':
            return queryset.filter(result__isnull=True)


class LogChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super(LogChangeList, self).__init__(*args, **kwargs)
        self.title = 'Execution Log'


class LogAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return LogChangeList

    readonly_fields = (
        'test',
        'result_display',
        'script_name',
        'start_time',
        'end_time',
        'duration',
        'total_duration',
        'test_duration',
        'note',
        'test_machine_ip',
        'browser_version_display',
        'platform_display',
        'console_log_display',
        'output_display',
        'get_jira_issues'
    )

    def get_fieldsets(self, request, obj=None):
        fieldsets = [
            (None,               {'fields': ['test', 'result_display', 'get_jira_issues', 'note']}),
            ('Test Environment', {'fields': ['browser_version_display', 'platform_display', 'test_machine_ip']}),
            ('Time',             {'fields': ['start_time', 'end_time', 'duration']}),
        ]

        if obj.console_log:
            fieldsets += [('Console Log', {'fields': ['console_log_display'], 'classes': ['collapse']})]

        if obj.output:
            fieldsets += [('Output', {'fields': ['output_display'], 'classes': ['collapse']})]

        return fieldsets

    list_display = (
        'test',
        'result_display',
        'execution_time',
        'duration',
        'browser_display',
        'platform_display'
    )

    list_filter = [
        LogResultFilter,
        LogExecutedFilter,
    ]

    search_fields = [
        'test',
        'script_name',
        'note',
        'console_log',
        'output',
        'browser',
        'platform'
    ]

    def get_jira_issues(self, obj):
        issues = get_issues(obj)

        if issues:
            ret_str = ''
            for i, issue in enumerate(issues):
                ret_str += '<a href="%s" target="_blank">%s</a>' % (issue['url'], issue['key'])
                if i < len(issues) - 2:
                    ret_str += ', '
            return ret_str
        elif issues is False:
            return '<span class="red"><i class="fa fa-exclamation-triangle" aria-hidden="true"></i> Contact with JIRA server could not be established.</span>'
        return '-'

    get_jira_issues.short_description = "JIRA Issues"
    get_jira_issues.allow_tags = True


    def result_display(self, obj):
        return get_result(obj.result)
    result_display.allow_tags = True
    result_display.short_description = "Result"

    def duration(self, obj):
        return format_number(obj.test_duration)

    def browser_version_display(self, obj):
        return capability_version_display(obj.browser, obj.browser_ver)
    browser_version_display.allow_tags = True
    browser_version_display.short_description = "Browser"

    def browser_display(self, obj):
        return capability_display(obj.browser)
    browser_display.allow_tags = True
    browser_display.short_description = "Browser"

    def platform_display(self, obj):
        return capability_version_display(obj.platform, obj.platform_ver)
    platform_display.allow_tags = True
    platform_display.short_description = "Platform"

    def execution_time(self, obj):
        return obj.end_time

    def console_log_display(self, obj):
        if not obj.console_log:
            return "-"
        ret_str = '<span class="typewriter">'
        for line in obj.console_log.split("\n"):
            ret_str += line + '<br>'
        ret_str += '</span>'
        return ret_str
    console_log_display.allow_tags = True
    console_log_display.short_description = "Console Log"

    def output_display(self, obj):
        if not obj.output:
            return "-"
        ret_str = '<span class="typewriter">'
        for line in obj.output.split("\n"):
            ret_str += line + '<br>'
        ret_str += '</span>'
        return ret_str
    output_display.allow_tags = True
    output_display.short_description = "Output"

    def report_to_jira(self, request, queryset):
        unique_obj = []

        for obj in queryset:
            if obj.result is False and not any(obj.test_id == tmp.test_id for tmp in unique_obj):
                unique_obj.append(obj)

        if not unique_obj:
            self.message_user(request, "Can only report failed test executions.", level=messages.WARNING)
            return

        success = 0
        failure = 0
        for obj in unique_obj:
            if report(obj):
                success += 1
            else:
                failure += 1

        if success == 1:
            self.message_user(request, 'Successfully reported 1 issue to JIRA.')
        elif success > 1:
            self.message_user(request, 'Successfully reported %i issues to JIRA.' % success)

        if failure == 1:
            self.message_user(request, 'Failed to report 1 issue to JIRA.', level=messages.ERROR)
        elif failure > 1:
            self.message_user(request, 'Failed to report %i issues to JIRA.' % failure, level=messages.ERROR)

        if success == 0 and failure == 0:
            self.message_user(request, 'Could not establish connection with JIRA.', level=messages.WARNING)

    report_to_jira.short_description = 'Report to JIRA'

    actions = [report_to_jira]

    ###
    def has_add_permission(self, request):
        return False

    # def has_delete_permission(self, request, obj=None):
    #     return False

    """def has_change_permission(self, request, obj=None):
        return False"""

admin.site.register(Log, LogAdmin)


class TestMachineBrowserFilter(SimpleListFilter):
    title = 'Browser'
    parameter_name = 'browser'

    def lookups(self, request, model_admin):
        return (
            ('CHROME',            ('Chrome')),
            ('EDGE',              ('Edge')),
            ('FIREFOX',           ('Firefox')),
            ('INTERNET EXPLORER', ('Internet Explorer')),
        )

    def queryset(self, request, queryset):
        queryset = queryset.filter(active=True)
        if self.value() == 'CHROME':
            return queryset.filter(chrome__isnull=False)
        elif self.value() == 'EDGE':
            return queryset.filter(edge__isnull=False)
        elif self.value() == 'FIREFOX':
            return queryset.filter(firefox__isnull=False)
        elif self.value() == 'INTERNET EXPLORER':
            return queryset.filter(internet_explorer__isnull=False)


class TestMachinePlatformFilter(SimpleListFilter):
    title = 'Platform'
    parameter_name = 'platform'

    def lookups(self, request, model_admin):
        return (
            ('LINUX',            ('Linux')),
            ('WINDOWS',          ('Windows')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'LINUX':
            return queryset.filter(operating_system='Linux')
        elif self.value() == 'WINDOWS':
            return queryset.filter(operating_system='Windows')


class TestMachineChangeList(ChangeList):
    def __init__(self, *args, **kwargs):
        super(TestMachineChangeList, self).__init__(*args, **kwargs)
        self.title = 'Test Machines'


class TestMachineAdmin(admin.ModelAdmin):
    def get_changelist(self, request, **kwargs):
        return TestMachineChangeList

    readonly_fields = [
        'url',
        'uuid',
        'active',
        'platform_display',
        'browsers_display',
    ]

    def get_fieldsets(self, request, obj=None):
        if obj is None:
            return [
                (None, {'fields': ['hostname']}),
            ]
        return [
            (None, {'fields': ['hostname', 'approved']}),
            (None, {'fields': ['active', 'platform_display', 'browsers_display']}),
        ]

    search_fields = [
        'hostname',
    ]

    list_filter = [
        'active',
        'approved',
        TestMachineBrowserFilter,
        TestMachinePlatformFilter,
    ]

    list_display = [
        'hostname_display',
        'platform_display',
        'browsers_list_display',
        'active',
        'approved',
    ]

    def hostname_display(self, obj):
        #return obj.hostname.upper()
        return obj.hostname
    hostname_display.short_description = "Hostname"

    def browsers_list_display(self, obj):
        ret_str = ''
        if obj.active:
            if obj.chrome:
                hint = '%s %s' % (browsers[0].title(), obj.chrome if obj.chrome is not True else '')
                ret_str += '<i class="fa fa-%s" title="%s"></i> ' % (browsers[0], hint)
            if obj.edge:
                hint = '%s %s' % (browsers[1].title(), obj.edge if obj.edge is not True else '')
                ret_str += '<i class="fa fa-%s" title="%s"></i> ' % (browsers[1], hint)
            if obj.firefox:
                hint = '%s %s' % (browsers[2].title(), obj.firefox if obj.firefox is not True else '')
                ret_str += '<i class="fa fa-%s" title="%s"></i> ' % (browsers[2], hint)
            if obj.internet_explorer:
                hint = '%s %s' % (browsers[3].title(), obj.internet_explorer if obj.internet_explorer is not True else '')
                ret_str += '<i class="fa fa-%s" title="%s"></i> ' % (browsers[3].replace(' ', '-'), hint)
        if not ret_str:
            ret_str = '-'
        return ret_str
    browsers_list_display.allow_tags = True
    browsers_list_display.short_description = 'Browsers'

    def browsers_display(self, obj):
        tmp_browsers = []
        if obj.active:
            if obj.chrome:
                hint = '%s %s' % (browsers[0].title(), obj.chrome if obj.chrome is not True else '')
                tmp_browsers.append('<i class="fa fa-%s"></i> %s' % (browsers[0], hint))
            if obj.edge:
                hint = '%s %s' % (browsers[1].title(), obj.edge if obj.edge is not True else '')
                tmp_browsers.append('<i class="fa fa-%s"></i> %s' % (browsers[1], hint))
            if obj.firefox:
                hint = '%s %s' % (browsers[2].title(), obj.firefox if obj.firefox is not True else '')
                tmp_browsers.append('<i class="fa fa-%s"></i> %s' % (browsers[2], hint))
            if obj.internet_explorer:
                hint = '%s %s' % (browsers[3].title(), obj.internet_explorer if obj.internet_explorer is not True else '')
                tmp_browsers.append('<i class="fa fa-%s"></i> %s' % (browsers[3].replace(' ', '-'), hint))
        if tmp_browsers:
            return "<br>".join(tmp_browsers)
        else:
            return "-"
    browsers_display.allow_tags = True
    browsers_display.short_description = 'Browsers'

    def platform_display(self, obj):
        return capability_version_display(obj.operating_system, obj.operating_system_ver)
    platform_display.allow_tags = True
    platform_display.short_description = 'Platform'

    def approve(self, request, queryset):
        changed_count = 0
        unchanged_count = 0

        for obj in queryset:
            if not obj.approved:
                obj.approved = True
                changed_count += 1
                obj.save()
            else:
                unchanged_count += 1
        if changed_count:
            if changed_count == 1:
                message_bit = "1 selected Test Machine was "
            else:
                message_bit = "%d selected Test Machine were " % changed_count
            self.message_user(request, "%s successfully approved." % message_bit)
        if unchanged_count:
            if unchanged_count == 1:
                message_bit = "1 selected Test Machine was "
            else:
                message_bit = "%d selected Test Machine were " % unchanged_count
            self.message_user(request, "%s already approved." % message_bit, level=messages.WARNING)

    def disapprove(self, request, queryset):
        changed_count = 0
        unchanged_count = 0

        for obj in queryset:
            if obj.approved:
                obj.approved = False
                changed_count += 1
                obj.save()
            else:
                unchanged_count += 1
        if changed_count:
            if changed_count == 1:
                message_bit = "1 selected Test Machine was "
            else:
                message_bit = "%d selected Test Machine were " % changed_count
            self.message_user(request, "%s successfully disapproved." % message_bit)
        if unchanged_count:
            if unchanged_count == 1:
                message_bit = "1 selected Test Machine was "
            else:
                message_bit = "%d selected Test Machine were " % unchanged_count
            self.message_user(request, "%s already disapproved." % message_bit, level=messages.WARNING)

    actions = [approve, disapprove]

    def save_model(self, request, obj, form, change):
        if obj.pk is None:
            obj.active = False
            obj.approved = True
            obj.operating_system = '-'
        obj.save()

admin.site.register(TestMachine, TestMachineAdmin)
