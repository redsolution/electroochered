# -*- coding: utf-8 -*-
import sys
from django.core.management.base import BaseCommand
from django.utils.log import getLogger
from sadiki.administrator.import_plugins import SADIKS_FORMATS, REQUESTION_FORMATS
from sadiki.administrator.models import ImportTask, IMPORT_START, IMPORT_ERROR, IMPORT_FINISH
from django.db import transaction
from sadiki.core.models import PREFERENCE_IMPORT_FINISHED, Preference, PREFERENCE_REQUESTIONS_IMPORTED

logger = getLogger('django.request')


class Command(BaseCommand):
    help = "Import requestions from file"

    def handle(self, *args, **options):
        import_tasks_ids = list(ImportTask.objects.filter(status=IMPORT_START).values_list('id', flat=True))
        import_tasks = ImportTask.objects.filter(id__in=import_tasks_ids)
#        первыми выполняем задания по импорту ДОУ
        sadik_list_tasks = import_tasks.filter(
            data_format__in=SADIKS_FORMATS)
        requestions_tasks = import_tasks.exclude(data_format__in=SADIKS_FORMATS)
        tasks = list(sadik_list_tasks) + list(requestions_tasks)
        for task in tasks:
#            запись в БД произойдет, если все ок, поэтому была убрана проверка
#            возможности сохранения для каждого объекта
            with transaction.commit_manually():
                try:
                    task.process()
#                    нам не нужно, чтобы при выполнении импорт останавливался
                except:
                    transaction.rollback()
#                    вместо этого логируем это дело, также происходит отправка письма
                    logger.error('Import error', exc_info=sys.exc_info(),)
                    task.status = IMPORT_ERROR
                    task.save()
                    transaction.commit()
                else:
                    transaction.commit()
        # если были импортированы заявки
        if ImportTask.objects.filter(id__in=import_tasks_ids, status=IMPORT_FINISH,
                                     data_format__in=REQUESTION_FORMATS, fake=False,
                                    errors=0).exists():
            Preference.objects.get_or_create(key=PREFERENCE_REQUESTIONS_IMPORTED)