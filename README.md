# OptiRun

## Package Installations:

| Package Name | Installation          |
| ---          | ---                   |
| Django       | `pip install django`  |
| Jira         | `pip install jira`    |
| or-tools	   | [Installation guidelines](https://developers.google.com/optimization/installing#python "Installing or-tools - Installing from binaries - Python") |


## Setup:

1. Install Python

```
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.create(name='<hostname>', domain='<hostname>')
```
