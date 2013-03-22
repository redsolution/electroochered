Требования к программному обеспечению
-------------------------------------

Операционная система - Debian GNU/linux 6.0 («Squeeze») 

Установленное ПО:

* веб-сервер Apache
* СУБД PostgreSQL
* Интерпретатор Python версии 2.6


1. Подготовка
--------------

1. Для установки системы «Электронная очередь в ДОУ» потребуется наличие следующих системных пакетов:

    * postgresql-8.4-postgis
    * proj
    * libpq-dev
    * python-psycopg2
    * python-crypto
    * python-reportlab
    * python-imaging
    * python-gdal
    * libapache2-mod-wsgi
    * python-setuptools
    * wkhtmltopdf
    
    * Команду `buildout` лучше устанавливать не из дистрибутива, а командой `sudo easy_install zc.buildout` так как Debian пакет `python-zc.buildout` работает с python 2.5. Для корректной работы системы нужен python 2.6*

2. Создайте нового системного пользователя и группы ``sadiki3`` без указания пароля с домашней директорией ``/srv/www/eturn/``: ::
    
    adduser --system --group --disabled-password --home=/srv/www/eturn/ --shell /bin/bash sadiki3

3. Необходимо настроить географические расширения для СУБД. Для этого необходимо от имени пользователя ``postgres`` выполнить команды: ::

    $ POSTGIS_SQL_PATH=`pg_config --sharedir`/contrib/postgis-1.5
    $ createdb -E UTF8 template_postgis
    $ createlang -d template_postgis plpgsql
    $ psql -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
    $ psql -d template_postgis -f $POSTGIS_SQL_PATH/postgis.sql
    $ psql -d template_postgis -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
    $ psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    $ psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
    $ psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

4. От имени пользоателя ``postgres`` cоздайте нового пользователя СУБД с паролем, без прав создания пользователей и баз, и принадлежащую ему пустую базу данных в PostgreSQL. Важно указать шаблон базы данных ``template_postgis``. Например: ::
    
    createuser -SRDP sadiki3
    createdb sadiki3 -T template_postgis -O sadiki3


2. Установка дистрибутива
-------------------------

Установка дистрибутива выполняется под учётной записью ``sadiki3``.

1. Скачайте дистрибутив ``sadiki3.tar.gz``  и распакуйте его содержимое в папку ``/srv/www/eturn/sadiki3/``.

2. Создайте рабочее окружение ``buildout`` с помощью команды ``buildout`` в каталоге ``sadiki3``::

    sadiki3@server:/srv/www/eturn/sadiki3$ buildout

  Выполнение команды может занять длительное время (до 10 минут).
  
3. Переименуйте файл в проекте ``sadiki/production.py.example`` в ``sadiki/production.py``.

4. Настройте параметры соединения с СУБД. Для этого укажите параметры соединения с сервером баз данных в файле ``/srv/www/eturn/sadiki3/eturn-django-settings.ini`` следующим образом::

    [database]
    DATABASE_USER: sadiki3
    DATABASE_PASSWORD: topsecret
    DATABASE_HOST: localhost
    DATABASE_PORT: 5432
    DATABASE_NAME: sadiki3

  Пароль должен совпадать с паролем, который был задан при создании пользователя СУБД

5. Настройка параметров системы. Необходимо добавить в конфигурационный файл ``/srv/www/eturn/sadiki3/eturn-django-settings.ini`` следующие строки::

    [secrets]
    SECRET_KEY:
    
    [email]
    DEFAULT_FROM_EMAIL: noreply@example.com
    SERVER_EMAIL: webmaster@example.com
    
    [admin mail]
    webmaster: webmaster@example.com
    
    [options]
    MUNICIPALITY_OCATO: 75401376000
    EMAIL_KEY_VALID: 3
    MAX_CHILD_AGE: 7
    NEW_YEAR_START: 31 12
    APPEAL_DAYS: 30
    
    [map]
    TILES_URL: http://{s}.somedomain.com/{z}/{x}/{y}.png
    TILES_SUBDOMAINS: subdomain1 subdomain2

- SECRET_KEY секретный ключ, можно получить запустив в консоли команду ``bin/django get_secret_key``
- DEFAULT_FROM_EMAIL адрес с которого будут отсылаться электронные сообщения
- SERVER_EMAIL адрес с которого будут отсылаться сообщения об ошибках
- webmaster адрес на который будут высылаться сообщения об ошибках
- MUNICIPALITY_OCATO номер окато муниципалитета
- EMAIL_KEY_VALID количество дней в течении которых активна ссылка для подтверждения почты или сброса пароля
- MAX_CHILD_AGE максимальный возратс ребенка в годах
- NEW_YEAR_START дата с коротой можно начать учебный год в формате "ДД ММ"
- APPEAL_DAYS количество дней на обжалование при неявке на зачисление
- TILES_URL - шаблон url сервера карт, {s}-подомен, выбираемый произвольным образом из списка TILES_SUBDOMAINS, {x},{y}-координаты,{z}-масштаб
- TILES_SUBDOMAINS - список поддоменов, разделенных пробелом

Если вы не хотите указывать свой сервер карт, то нужно удалить раздел ``map``, при этом будет использоваться стандартный сервер tile.openstreetmap.org

3. Настройка веб-сервера
------------------------

Ниже приведены инструкции для настройки сервера Apache.
Для других веб-серверов настройки выполняются аналогично, согласно документации веб-сервера.

1. В директории ``/srv/www/eturn/sadiki3/`` от имени пользователя ``sadiki3`` выполните команду: ::

    sadiki3@server:/srv/www/eturn/sadiki3$ bin/django collectstatic -l --noinput

  В результате в текущей директории должна появиться папка ``/static/``  с символическими ссылками для
  статичных файлов проекта (каскадные таблицы стилей, файлы Javascript).

2. Скопируйте в папку Apache конфигурационный файл ``apache_sample_conf``, если Вы хотите, чтобы система была доступна по доменному имени или ``apache_sample_conf_local``, если ваш сайт будет доступен только на локальном компьютере пользователя. Переименуйте скопированный конфигурационный файл в ``sadiki3`` В конфигурационном файле необходимо заменить <site.tld> на ваш домен и <name> на имя пользователя("sadiki3"). ::

    root@server: cp apache_sample_conf /etc/apache2/sites-available/sadiki3

3. Создайте папку для хранения логов, которая указана в конфигурационном файле(по умолчанию каталог с логами ``/var/log/apache2/``). Владельцм должен быть root и  у файла дожны быть установлены права 740.

4. От имени пользователя sadiki3 cоздайте папку public_html в домашней папке пользователя sadiki3 и создайте символьные ссылки на ``sadiki3/bin/django.wsgi``, ``sadiki3/static/`` и ``sadiki/media/upload``::

    sadiki3@server:/srv/www/eturn/$ mkdir public_html
    sadiki3@server:/srv/www/eturn/$ ln -s /srv/www/eturn/sadiki3/bin/django.wsgi public_html/django.wsgi
    sadiki3@server:/srv/www/eturn/$ mkdir public_html/media
    sadiki3@server:/srv/www/eturn/$ ln -s /srv/www/eturn/sadiki3/media/upload public_html/media/upload
    sadiki3@server:/srv/www/eturn/$ ln -s /srv/www/eturn/sadiki3/static/ public_html/static

5. От имени пользователя sadiki3 cоздайте папку для загружаемых файлов ``/srv/www/eturn/sadiki3/media/upload``

6. Для выполнения фоновых задач системы задайте расписание для команд.

   Пример файла cron: ::

    crontab -lu sadiki3

    # m h  dom mon dow   command
      1 * 	*   *   *    /srv/www/eturn/sadiki3/bin/django <command>

Описание команд см. ниже.


4. Начальное наполнение базы данных
-----------------------------------

1. В директории ``/srv/www/eturn/sadiki3/`` от имени пользователя ``sadiki3`` выполните команды: ::

    sadiki3@server:/srv/www/eturn/sadiki3$ bin/django syncdb --noinput --migrate
    sadiki3@server:/srv/www/eturn/sadiki3$ bin/django loaddata sadiki/core/fixtures/deploy_data.json
    sadiki3@server:/srv/www/eturn/sadiki3$ bin/django updatepermissions

2. Создайте суперпользователя с помощью команды: ::

    sadiki3@server:/srv/www/eturn/sadiki3$ bin/django create_administrator

3. Активируйте созданную конфигурацию Apache.::

    root@server:/home/root$ a2ensite sadiki3

4. Активируйте модуль ``mod_rewrite`` и перезапустите Apache ::

    root@server:/home/root$ a2enmod rewrite
    root@server:/home/root$ apachectl restart

5. Откройте в браузере страницу: http://example.com/adm, где вместо
   example.com указанный вами домен для системы. Должна появиться форма входа
   в административный раздел.

6. Описание системных команд
-----------------------------

**confirmation_expire**


Команда удаления заявок без документального подтверждения. Запуск - ежедневно. ::

    /srv/www/eturn/sadiki3/bin/django confirmation_expire

**auto_change_status**

Команда автоматического отслеживания сроков явки. Запуск - ежедневно. ::

    /srv/www/eturn/sadiki3/bin/django auto_change_status

**create_reports**

Команда создания отчётов. Запуск - ежеквартально. ::

    /srv/www/eturn/sadiki3/bin/django create_reports

