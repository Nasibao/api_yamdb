import csv
import glob
import os

from django.core.management.base import BaseCommand

from reviews.models import (
    Category,
    Comment,
    Genre,
    GenreTitle,
    Review,
    Title,
    User,
)

MODELS_CONTAINER = [
    User,
    Category,
    Genre,
    Title,
    GenreTitle,
    Review,
    Comment,
]


class Command(BaseCommand):
    help = (
        "Cкрипт , который наполняет БД данными из CSV файлов."
        "Пример: `python manage.py load-csv static/data"
    )

    def add_arguments(self, parser):
        parser.add_argument("csv_folder", help="path to csv file", type=str)

    def fields_checker(self, fields_name, model_fields):
        for i, _ in enumerate(fields_name):
            fields_name[i] = fields_name[i].lower().replace(" ", "_")
            if not fields_name[i] in model_fields:
                return False
        return True

    def file_to_model(self, all_files, all_models):
        model_file_dict = {}
        csv_file_list = []
        for csv_file in all_files:
            if not os.path.isfile(csv_file):
                return (
                    "Когда вы вызываете функцию, вы должны"
                    "передать путь к файлам csv"
                )
            mod_name = csv_file.replace("_", "")
            mod_name = mod_name.split(os.path.sep).pop().split(".")[0]
            csv_file_list.append((csv_file, mod_name))
        for model in all_models:
            for file_name, compare_name in csv_file_list:
                if str(model.__name__).lower() == compare_name:
                    model_file_dict[model] = file_name
        return model_file_dict

    def handle(self, *args, **options):
        csv_folder = options.get("csv_folder", "")
        all_files = glob.glob(csv_folder + "/*.csv")

        for (key, value) in self.file_to_model(
            all_files,
            MODELS_CONTAINER,
        ).items():

            fields_name = []
            with open(value, "r", encoding="utf-8") as f:
                reader = csv.reader(f, delimiter=",", quotechar='"')
                fields_name = next(reader)
                entity_list = []
                for raw in reader:
                    dict_data = {
                        fields_name[key]: field
                        for key, field in (enumerate(raw))
                    }
                    entity_list.append(key(**dict_data))
                try:
                    key.objects.bulk_create(entity_list)
                    print(f"finish {key}")
                except Exception as e:
                    return f"Данные уже имеются! {e}"
        return "Файл CSV успешно выгружен."
