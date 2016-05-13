from django import forms


class TestCaseAdminForm(forms.ModelForm):
    # In the future: extend this function to check more stuff?
    # For instance check if it imports selenium and if selenium functions are used
    # Check if it is a unit test, etc.
    def clean_script(self):
        script = self.cleaned_data.get("script", False)
        # This check won't be necessary later, because blank=True will be removed from model
        if script == None:
            return script
        else:
            filename = script.name
            if not filename.endswith('.py'):
                raise forms.ValidationError('Only .py files are allowed.')
        return script

    def render(self, name, value, attrs=None):
        return '<script type="text/javascript">callMyFunction(sdf)</script>'

    class Media:
        js = ('js/test_case_admin.js',)


class ScheduleAdminForm(forms.ModelForm):

    class Media:
        js = ('schedule-admin.js',)
