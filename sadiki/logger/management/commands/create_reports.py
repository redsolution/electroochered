# -*- coding: utf-8 -*-
from django.core.management.base import BaseCommand
from sadiki.core.models import AgeGroup
from sadiki.logger.models import Logger, Report, \
    REPORTS_CHOICES, REPORT_DECISION_CHOICES
import datetime
from sadiki.logger.views import REPORTS_INFO


class Command(BaseCommand):
    help_text = '''Usage: manage.py create_reports'''

    def handle(self, *args, **options):
#        пробегаемся по всем видам отчетов
        for report_type, report_name in dict(REPORTS_CHOICES).iteritems():
            reports = Report.objects.filter(type=report_type).order_by("-to_date")
            to_date = datetime.date.today() - datetime.timedelta(days=1)
            if reports.exists():
                from_date = reports[0].to_date
            elif Logger.objects.all().exists():
                from_date = Logger.objects.all().order_by("datetime")[0].datetime.date()
            else:
                from_date = to_date
    #        если в форме есть поле age_group то в отчете учитываются группы
            if "age_group" in REPORTS_INFO["parameters"][report_type]:
                for age_group in AgeGroup.objects.all():
                    if "decision" in REPORTS_INFO["parameters"][report_type]:
                        for decision_type in dict(REPORT_DECISION_CHOICES).keys():
                            Report.objects.create_report(report_type=report_type,
                            from_date=from_date, to_date=to_date, age_group=age_group,
                            decision_type=decision_type)
                    else:
                        Report.objects.create_report(report_type=report_type,
                            from_date=from_date, to_date=to_date, age_group=age_group)
            else:
                Report.objects.create_report(report_type=report_type,
                    from_date=from_date, to_date=to_date)

