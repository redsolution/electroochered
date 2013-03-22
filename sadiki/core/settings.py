# -*- coding: utf-8 -*-

#      Настройки для системы

# Немедленное зачисление
IMMEDIATELY_DISTRIBUTION_NO = 0              # Недоступно всегда
IMMEDIATELY_DISTRIBUTION_YES = 1             # Доступно всегда
IMMEDIATELY_DISTRIBUTION_FACILITIES_ONLY = 2 # Доступно всегда только для определенных категорий льгот

# Желаемая дата поступления
DESIRED_DATE_NO = 0         # нет
DESIRED_DATE_NEXT_YEAR = 1  # 1 сентября следующего года
DESIRED_DATE_SPEC_YEAR = 2  # 1 сентября любого указанного года (указывается в заявлении)
DESIRED_DATE_ANY = 3        # любая дата  (указывается в заявлении)

# Электронные путевки
ETICKET_ONLY = 0    # Зачисление в ДОУ строго по путевкам
ETICKET_MIXED = 1   # зачисление в ДОУ по путевкам и документам на основании списков, переданных РУО,
ETICKET_NO = 2      # зачисление только по спискам из РУО

# Временное зачисление
TEMP_DISTRIBUTION_NO = 0  # Временного зачисления нет
TEMP_DISTRIBUTION_YES = 1 # Временное зачисление есть

# Хранение льгот
FACILITY_STORE_NO = 0   # хранятся только категории
FACILITY_STORE_YES = 1  # хранятся все данные о льготах

# Квотирование льгот
FACILITY_QUOTA_NO = 0       # Нет квотирования
FACILITY_QUOTA_GLOBAL = 1   # квотируется % от общего количества мест в ДОУ
FACILITY_QUOTA_GROUP = 2    # квотируется % от общего количества мест в ДОУ отдельно для каждой возрастной группы

FACILITY_QUOTA = FACILITY_QUOTA_NO

#Системные категории льгот
FACILITY_TRANSFER_CATEGORY = 100
BENEFIT_SYSTEM_MIN = 100
WITHOUT_BENEFIT_PRIORITY = 0

# Желаемые ДОУ
DESIRED_SADIKS_ONLY = 0       # зачисление только в приоритетные ДОУ
DESIRED_SADIKS_CHOICE = 1   # можно указать допустимость зачисления в другое ДОУ
DESIRED_SADIKS_ANY = 2      # если мест нет, зачисление в произвольное ДОУ, где имеются свободные места

DESIRED_SADIKS = DESIRED_SADIKS_CHOICE

# Срок подтверждения документов
DOCUMENTS_VALID = 3

# Срок явки после предоставления места
DISTRIBUTION_CONFIRM_VALID = 3
