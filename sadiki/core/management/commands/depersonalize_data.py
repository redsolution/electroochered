# -*- coding: utf-8 -*-
import time
import logging
import os
import sys
import tarfile
import shutil
import itertools

from django.core import management
from django.apps import apps
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType


class Command(management.base.BaseCommand):
    # help = "Dumps or loads depersonalized json data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--export',
            action='store_true',
            dest='export',
            default=False,
        )
        parser.add_argument(
            '--import',
            action='store_true',
            dest='import',
            default=False,
        )
        parser.add_argument('file_name', nargs='?')
        parser.add_argument('-c', '--comment', action='count', default=0)
        parser.add_argument('-q', '--quiet', action='count', default=0)

    def handle(self, *args, **options):
        # configuring logging
        quiet = options['quiet']
        verbose = options['comment']
        log_level = logging.WARN + 10 * quiet - 10 * verbose
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s, %(levelname)s: %(message)s',
            datefmt='%m.%d.%Y %H:%M:%S'
        )

        if not (options['export'] ^ options['import']):
            print 'Error!'
            print ('You must specify exactly one of this option: '
                   '--export or --import')
            sys.exit()
        file_name = options.get('file_name') or 'data.tar.gz'
        file_name = os.path.abspath(file_name)
        dir_name = 'temp_djson_data'
        dir_name_suffix = 1
        # ищем свободное имя для временной директории с дампом
        while os.path.exists(dir_name):
            dir_name = 'temp_djson_data_' + str(dir_name_suffix)
            dir_name_suffix += 1

        if options['export']:
            if os.path.exists(file_name):
                user_input = raw_input(
                    'File {} already exists! Overwrite it? (y/n): '.format(
                        file_name)
                )
                while user_input not in ('y', 'n'):
                    user_input = raw_input('Incorrect input!\n')
                if user_input == 'n':
                    print 'Exit...'
                    sys.exit()
            model_list = list(
                itertools.chain.from_iterable(
                    app_config.get_models()
                    for app_config in apps.get_app_configs()
                    if app_config.models_module is not None)
            )
            sorted_model_list = sort_dependencies(model_list)
            model_labels = [
                '.'.join([model._meta.app_label, model._meta.model_name])
                for model in sorted_model_list
            ]
            logging.info(u"Начинаю экспорт, запускается dumpdata")
            start_time = time.time()
            try:
                os.mkdir(dir_name)
            except OSError as e:
                print 'Error!'
                print e
                sys.exit(1)
            for model_number, model_label in enumerate(model_labels):
                model_dir_name = os.path.join(dir_name,
                                              'model{}'.format(model_number+1))
                try:
                    os.mkdir(model_dir_name)
                    output_fname = os.path.join(model_dir_name, 'data.djson')
                    management.call_command(
                        'dumpdata',
                        model_label,
                        '--format', 'djson',
                        '--output', output_fname,
                    )
                except Exception as e:
                    print 'Error!'
                    print e
                    shutil.rmtree(dir_name)
                    sys.exit(1)
            try:
                tar = tarfile.open(file_name, 'w:gz')
            except Exception as e:
                print 'Error!'
                print e
                sys.exit(1)
            try:
                tar.add(dir_name, arcname='')
                tar.close()
            except Exception as e:
                print 'Error!'
                print e
                tar.close()
                if os.path.exists(file_name):
                    os.remove(file_name)
                shutil.rmtree(dir_name)
                sys.exit(1)
            shutil.rmtree(dir_name)
            logging.info(u"Экспорт завершен, время исполнения: {}:{}".format(
                int(time.time() - start_time) / 60,
                int(time.time() - start_time) % 60,
            ))
            print 'Dump saved successfully to {}'.format(file_name)
        else:
            if not os.path.isfile(file_name):
                print 'Error!'
                print 'No such regular file: {}'.format(file_name)
                sys.exit(1)
            management.call_command('flush')
            Permission.objects.all().delete()
            ContentType.objects.all().delete()
            try:
                tar = tarfile.open(file_name)
                tar.extractall(path=dir_name)
            except Exception as e:
                print 'Error!'
                print e
                if os.path.isdir(dir_name):
                    shutil.rmtree(dir_name)
                sys.exit(1)
            model_number = 1
            model_dir_name = os.path.join(dir_name, 'model1')
            while os.path.isdir(model_dir_name):
                print 'Loading model {} ...'.format(model_number)
                parts = [os.path.join(model_dir_name, fname)
                         for fname in os.listdir(model_dir_name)]
                try:
                    for part_fname in parts:
                        management.call_command('loaddata', part_fname)
                except Exception as e:
                    print 'Error!'
                    print e
                    shutil.rmtree(dir_name)
                    tar.close()
                    sys.exit(1)
                model_number += 1
                model_dir_name = os.path.join(dir_name,
                                              'model{}'.format(model_number))
            shutil.rmtree(dir_name)
            tar.close()
            print 'Dump from {} restored successfully'.format(file_name)


def sort_dependencies(model_list):
    """
    Сортирует список моделей так, чтобы любая модель находилась в списке после
    всех моделей, от которых имеются зависимости natural key, ForeignKey,
    ManyToMany.
    """
    model_dependencies = []
    for model in model_list:
        # Add any explicitly defined dependencies
        if hasattr(model, 'natural_key'):
            deps = getattr(model.natural_key, 'dependencies', [])
            if deps:
                deps = [apps.get_model(dep) for dep in deps]
        else:
            deps = []
        # Now add a dependency for any FK relation with a model that
        # defines a natural key
        for field in model._meta.fields:
            if hasattr(field.rel, 'to'):
                rel_model = field.rel.to
                if rel_model != model:
                    deps.append(rel_model)
        # Also add a dependency for any simple M2M relation with a model
        # that defines a natural key.  M2M relations with explicit through
        # models don't count as dependencies.
        for field in model._meta.many_to_many:
            if field.rel.through._meta.auto_created:
                rel_model = field.rel.to
                if hasattr(rel_model, 'natural_key') and rel_model != model:
                    deps.append(rel_model)
        model_dependencies.append((model, deps))

    model_dependencies.reverse()
    # Now sort the models to ensure that dependencies are met. This
    # is done by repeatedly iterating over the input list of models.
    # If all the dependencies of a given model are in the final list,
    # that model is promoted to the end of the final list. This process
    # continues until the input list is empty, or we do a full iteration
    # over the input models without promoting a model to the final list.
    # If we do a full iteration without a promotion, that means there are
    # circular dependencies in the list.
    sorted_model_list = []
    while model_dependencies:
        skipped = []
        changed = False
        while model_dependencies:
            model, deps = model_dependencies.pop()

            # If all of the models in the dependency list are either already
            # on the final model list, or not on the original serialization list,
            # then we've found another model with all it's dependencies satisfied.
            found = True
            for candidate in ((d not in model_list or d in sorted_model_list)
                              for d in deps):
                if not candidate:
                    found = False
            if found:
                sorted_model_list.append(model)
                changed = True
            else:
                skipped.append((model, deps))
        if not changed:
            raise RuntimeError(
                "Can't resolve dependencies for %s in serialized app list." %
                ', '.join('%s.%s' % (model._meta.app_label, model._meta.object_name)
                for model, deps in sorted(skipped, key=lambda obj: obj[0].__name__))
            )
        model_dependencies = skipped

    return sorted_model_list
