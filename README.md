# OptiRun

Package Installations:

| Package Name | Installation Command ('pip') |
| ---          | ---                          |
| Django       | `pip install django`         |
| Jira         | `pip install jira`           |

Setup:
```
python manage.py shell
>>> from django.contrib.sites.models import Site
>>> Site.objects.create(name='<hostname>', domain='<hostname>')
```