import copy
import inspect

import threading
from threading import Thread


from datetime import datetime
import locale

import pandas as pd

from docxtpl import DocxTemplate

from django.core.mail import send_mail
from django.conf import settings
from django.forms.models import model_to_dict
from django.db import models

from options import models as options_models

from options.models import *


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


def parse_str_to_date(date_str):
    try:
        date = datetime.strptime(date_str, '%Y-%m-%d %H:%M:%S')
        return date
    except:
        pass


class EmailThread(threading.Thread):
    def __init__(self, subject, html_content, recipient_list):
        self.subject = subject
        self.recipient_list = recipient_list
        self.html_content = html_content
        threading.Thread.__init__(self)

    def run (self):
        msg = EmailMessage(self.subject, self.html_content, settings.EMAIL_HOST_USER, self.recipient_list)
        msg.content_subtype = "html"
        msg.send()


class AnimalRequest(models.Model):
    animal_shelter = models.ForeignKey('AnimalInShelter', on_delete=models.CASCADE)
    owner_name = models.CharField(max_length=127)
    owner_contact = models.CharField(max_length=127)

    datetime = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} @{self.owner_name}"

    def create_request(ais, owner_name, owner_contact):
        EmailThread(
            f'Запрос на №{ais.animal.identification_number}',
            f'ФИО: {owner_name}\nrКонтактные данные: {owner_contact}',
            [ais.shelter.email],
        )

        request = AnimalRequest.objects.create(
            animal_shelter=ais, owner_name=owner_name, owner_contact=owner_contact)

        return request


class OwnerEntity(models.Model):
    organization_name = models.CharField(max_length=127)
    address = models.CharField(max_length=127)
    contacts = models.CharField(max_length=127)

    telephone = models.CharField(max_length=127)
    owner_name = models.CharField(max_length=127)
    owner_contact = models.CharField(max_length=127)

    def __str__(self):
        return self.organization_name

    def from_dict(row):
        owner = OwnerEntity.objects.filter(
            organization_name=row['owner_entity__organization_name'],
            owner_name=row['owner_entity__owner_name']).first()

        if owner is None:
            owner = OwnerEntity()

        keys = [key for key in row.keys() if key.split('__')[0] == 'owner_entity']

        for col in keys:
            field, val = col.split('__')[1], row[col]

            setattr(owner, field, val)

        owner.save()

        return owner


class OwnerIndividual(models.Model):
    name = models.CharField(max_length=127)
    passport_series = models.CharField(max_length=127)
    passport_number = models.CharField(max_length=127)
    passport_issued  = models.CharField(max_length=127)
    passport_date   = models.CharField(max_length=127)
    passport_address = models.CharField(max_length=127)
    contact = models.CharField(max_length=127)

    def __str__(self):
        return self.name

    def from_dict(row):
        owner = OwnerIndividual.objects.filter(
            name=row['owner_individual__name']).first()

        if owner is None:
            owner = OwnerIndividual()

        keys = [key for key in row.keys() if key.split('__')[0] == 'owner_individual']

        for col in keys:
            field, val = col.split('__')[1], row[col]

            setattr(owner, field, val)

        owner.save()

        return owner


class Animal(models.Model):
    SIZES = [
        ('1', 'Средний'),
        ('2', 'Малый'),
        ('3', 'Крупный'),
        ('4', 'Большой')
    ]

    identification_number = models.CharField(max_length=126)
    cart_number = models.CharField(max_length=126)
    kind = models.ForeignKey(AnimalKind, on_delete=models.CASCADE)
    age = models.IntegerField()
    weight = models.FloatField()
    name = models.CharField(max_length=126)
    sex = models.ForeignKey(AnimalSex, on_delete=models.CASCADE)
    breed = models.ForeignKey(AnimalBreed, on_delete=models.CASCADE)
    color = models.ForeignKey(AnimalColor, on_delete=models.CASCADE)
    wool = models.ForeignKey(AnimalWool, on_delete=models.CASCADE)
    ears = models.ForeignKey(AnimalEars, on_delete=models.CASCADE)
    tail = models.ForeignKey(AnimalTail, on_delete=models.CASCADE)
    size = models.CharField(max_length=1, choices=SIZES)

    special_signs = models.TextField()
    is_socialization = models.BooleanField(default=False)

    sterialization_status = models.CharField(max_length=127, blank=True)
    sterialization_veterinarian_name = models.CharField(max_length=127, blank=True)

    owner_entity = models.ForeignKey(OwnerEntity, on_delete=models.CASCADE, blank=True, null=True)
    owner_individual =  models.ForeignKey(OwnerIndividual, on_delete=models.CASCADE, blank=True, null=True)

    def __str__(self):
        return f"{self.identification_number} @{self.name}"

    @property
    def image(self):
        return self.asd

    @property
    def size_name(self):
        return dict(self.SIZES)[self.size]

    @property
    def current_shelter(self):
        return AnimalInShelter.objects.filter(animalcapture__animal=self).last()

    @property
    def current_shelter_name(self):
        return self.current_shelter.shelter.name

    @property
    def current_shelter_address(self):
        return self.current_shelter.shelter.address

    @property
    def current_shelter_email(self):
        return self.current_shelter.shelter.email

    def to_dict(self):
        params = copy.copy(self.__dict__)

        for key in self.__dict__:
            if not key.startswith('owner') and key.endswith('_id'):
                params[key[:-3]] = getattr(self, key[:-3]).name

        params['size'] = dict(self.SIZES)[params['size']]

        return params

    def from_dict(row):
        animal = Animal.objects.filter(
            identification_number=row['animal__identification_number']).first()

        if animal is None:
            animal = Animal()

        keys = [key for key in row.keys() if key.split('__')[0] == 'animal']

        for col in keys:
            field, val = col.split('__')[1], row[col]

            if field.startswith('@'):
                field = field[1:]
                OptionModel = eval(f'Animal{field.capitalize()}')
                obj = OptionModel.objects.filter(name=val).first()

                if obj is None:
                    obj = OptionModel()

                obj.name = val
                obj.save()
                val = obj

            setattr(animal, field, val)

        if not pd.isna(row['owner_entity__organization_name']):
            animal.owner_entity = OwnerEntity.from_dict(row)

        if not pd.isna(row['owner_individual__name']):
            animal.owner_individual = OwnerIndividual.from_dict(row)

        animal.save()

        return animal

    def filter_by_params(params, is_socialization=None):
        animals = Animal.objects.filter(
            kind__name=params['kind'],
            sex__name='Мужской' if params['sex'] else 'Женский',
            weight__gte=params['min_weight'],
            weight__lte=params['max_weight'],
            age__gte=params['min_age'],
        )

        if not is_socialization is None:
            animals = animals.filter(is_socialization=is_socialization)

        return [animal for animal in animals if animal.current_shelter.leave_reason is None]


class AnimalVacine(models.Model):
    VACINES = [
        ('1', 'Нобивак Трикат Трио Леоминор'),
        ('2', 'Nobivac Tricat Trio+R'),
        ('3', 'Нобивак Трикат Трио'),
        ('4', 'Астерион DHPPi-L'),
        ('5', 'Нобивак Трикат'),
        ('6', 'Пуревакс FelV'),
        ('7', 'Нобивак DHPPI'),
        ('8', 'Нобивак Lepto'),
        ('9', 'Мультикан-6'),
        ('10', 'Мультифел-4'),
        ('11', 'Мультикан-4'),
        ('12', 'Мультикан-8'),
        ('13', 'Мультикан-9'),
        ('14', 'Бешенство'),
        ('15', 'Мультикан'),
        ('17', 'Леоминор'),
        ('18', 'Астерион'),
        ('19', 'Рабикан'),
        ('20', 'Нобивак'),
        ('21', 'Lepto')]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    name = models.CharField(max_length=2, choices=VACINES)
    series = models.CharField(max_length=31)
    date = models.DateField()

    def __str__(self):
        return f"{self.name} @{self.animal}"

    @property
    def vacine_name(self):
        return dict(self.VACINES)[self.name]

    def from_dict(row):
        animal = Animal.from_dict(row)

        numbers = eval(row['animal_vacine__numbers'])
        if numbers[0] == 'nan':
            return

        dates = eval(row['animal_vacine__dates'])
        names = eval(row['animal_vacine__names'])
        series = eval(row['animal_vacine__series'])

        for number, date, name, series in zip(numbers, dates, names, series):
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

            vacine = AnimalVacine.objects.filter(
                animal=animal, date=date, name=name).first()

            if vacine is None:
                vacine = AnimalVacine()

            vacine.animal = animal
            vacine.name = name
            vacine.series = series if not series == 'nan' else ''
            vacine.date = date
            vacine.save()


class AnimalDrug(models.Model):
    DRUGS = [
        ('1', 'Паразицид-суспензия'),
        ('2', 'Дана СПОТ-ОН/Алевит'),
        ('3', 'Инспектор Тотал К'),
        ('4', 'Блох нэт/ альвет'),
        ('5', 'Каниквантел Барс'),
        ('6', 'Барс для кошек'),
        ('7', 'Рольф клуб 3D'),
        ('8', 'Стронгхолд'),
        ('9', 'Рольф Клуб'),
        ('10', 'Стронхолд'),
        ('11', 'Инсектал'),
        ('12', 'Празител'),
        ('13', 'Азинокс'),
        ('14', 'Тронцил'),
        ('15', 'Дронтал'),
        ('16', 'Прател'),
        ('17', 'БАРС')
    ]

    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    name = models.CharField(max_length=2, choices=DRUGS)
    dose = models.CharField(max_length=31)
    date = models.DateField()

    def __str__(self):
        return f"{self.drug_name} @{self.animal}"

    @property
    def drug_name(self):
        return dict(self.DRUGS)[self.name]

    def from_dict(row):
        animal = Animal.from_dict(row)

        numbers = eval(row['animal_drug__numbers'])
        dates = eval(row['animal_drug__dates'])
        names = eval(row['animal_drug__names'])
        doses = eval(row['animal_drug__doses'])

        for number, date, name, dose in zip(numbers, dates, names, doses):
            date = datetime.strptime(date, '%Y-%m-%d %H:%M:%S')

            drug = AnimalDrug.objects.filter(
                animal=animal, date=date, name=name).first()

            if drug is None:
                drug = AnimalDrug()

            drug.animal = animal
            drug.name = name
            drug.dose = dose
            drug.date = date

            drug.save()


class AnimalCapture(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    district = models.CharField(max_length=127)
    address = models.CharField(max_length=127)
    act = models.CharField(max_length=31)

    certificater = models.CharField(max_length=127)
    certificater_date = models.DateField(blank=True, null=True)

    def __str__(self):
        return f'{self.act} @{self.animal}'

    def from_dict(row):
        animal = Animal.from_dict(row)

        capture = AnimalCapture.objects.filter(
            animal=animal,
            act=row['animal_capture__act']).first()

        if capture is None:
            capture = AnimalCapture()

        animal = Animal.from_dict(row)

        capture.animal = animal
        capture.certificater_date = parse_str_to_date(row['animal_capture__certificater_date'])

        for field in ['district', 'address', 'act', 'certificater']:
            setattr(capture, field, row['animal_capture__' + field])

        capture.save()

        return capture


class AnimalInspection(models.Model):
    animal = models.ForeignKey(Animal, on_delete=models.CASCADE)
    anamnes = models.CharField(max_length=127)
    weight = models.FloatField()
    date = models.DateField(blank=True)

    def __str__(self):
        return f"{self.anamnes} @{self.animal}"

    def from_dict(row):
        animal = Animal.from_dict(row)
        date = parse_str_to_date(row['animal_inspection__date'])

        inspection = AnimalInspection.objects.filter(
            animal=animal,
            date=date).first()

        if inspection is None:
            inspection = AnimalInspection()

        inspection.animal = animal
        inspection.date = date
        inspection.weight = row['animal__weight']
        inspection.anamnes = row['animal_inspection__anamnes']
        inspection.save()

        return inspection


class AnimalInShelter(models.Model):
    shelter = models.ForeignKey('shelter.Shelter', on_delete=models.CASCADE)
    shelter_staff = models.ForeignKey('shelter.ShelterStaff', on_delete=models.CASCADE)
    animalcapture = models.ForeignKey(AnimalCapture, on_delete=models.CASCADE)

    aviary_number = models.CharField(max_length=31)
    arrived_act = models.CharField(max_length=127)
    arrived_date = models.DateField()

    leave_act = models.CharField(max_length=127, blank=True)
    leave_reason = models.ForeignKey(AnimalLeaveReason, on_delete=models.CASCADE, blank=True, null=True)
    leave_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.shelter} @{self.animal}"

    @property
    def image(self):
        return f"{shelter.address}/{animal.cart_number}.jpg"

    @property
    def animal(self):
        return self.animalcapture.animal

    def from_dict(row, animalcapture, shelter, shelter_staff):
        a_shelter = AnimalInShelter.objects.filter(
            animalcapture=animalcapture, shelter=shelter,
            arrived_act=row['animal_shelter__arrived_act']).first()

        if a_shelter is None:
            a_shelter = AnimalInShelter()

        arrived_date = parse_str_to_date(row['animal_shelter__arrived_date'])
        leave_date = parse_str_to_date(row['animal_shelter__leave_date'])

        a_shelter.arrived_date = arrived_date
        a_shelter.leave_date = leave_date

        a_shelter.shelter_staff = shelter_staff
        a_shelter.animalcapture = animalcapture; a_shelter.shelter = shelter;
        a_shelter.aviary_number = row['animal_shelter__aviary_number']
        a_shelter.arrived_act = row['animal_shelter__arrived_act']
        a_shelter.leave_act = row['animal_shelter__leave_act']
        a_shelter.leave_reason = row['animal_shelter__leave_reason']
        a_shelter.save()

        return a_shelter

    def filter_by_params(params, is_socialization=None):
        animals = AnimalInShelter.objects.filter(
            animalcapture__animal__kind__name=params['kind'],
            animalcapture__animal__sex__name='Мужской' if params['sex'] else 'Женский',
            animalcapture__animal__weight__gte=params['min_weight'],
            animalcapture__animal__weight__lte=params['max_weight'],
            animalcapture__animal__age__gte=params['min_age'],
        )

        if not is_socialization is None:
            animals = animals.filter(animalcapture__animal__is_socialization=is_socialization)


        return animals

    def gerenerate_animal_cart_docx(self):
        doc = DocxTemplate('docx_templates/animal_card_template.docx')

        params = {
            'today': datetime.now().strftime('«%d» %B %Y год'),
            'is_dog': '✓' if self.animal.kind.name == 'Собака' else '',
            'is_cat': '✓' if self.animal.kind.name == 'Кошка' else '',
            'is_socialization': 'Да' if self.animal.is_socialization else 'Нет',
            'staff_name': self.shelter_staff.name,
        }

        for key, value in model_to_dict(self.shelter).items():
            params['shelter__'+key] = str(value)

        for key, value in model_to_dict(self).items():
            params['animalinshelter__'+key] = str(value)

        for key, value in model_to_dict(self.animalcapture).items():
            params['animalcapture__'+key] = str(value)

        for key, value in self.animal.to_dict().items():
            params['animal__'+key] = str(value)

        if not self.animal.owner_entity is None:
            for key, value in model_to_dict(self.animal.owner_entity).items():
                params['owner_entity__'+key] = str(value)

        if not self.animal.owner_individual is None:
            for key, value in model_to_dict(self.animal.owner_individual).items():
                params['owner_individual__'+key] = str(value)

        params['drugs_list'] = [{
            'label': i+1,
            'date': drug.date,
            'name': drug.drug_name,
            'dose': drug.dose
        } for i, drug in enumerate(self.animal.animaldrug_set.all())]

        params['vacines_list'] = [{
            'label': i+1,
            'date': vactine.date,
            'name': vactine.vacine_name,
            'series': vactine.series
        } for i, vactine in enumerate(self.animal.animalvacine_set.all())]

        params['inspection_list'] = [{
            'label': i+1,
            'date': inspection.date,
            'weight': inspection.weight,
            'anamnes': inspection.anamnes
        } for i, inspection in enumerate(self.animal.animalinspection_set.all())]


        for key, value in params.items():
            if value == 'None' or value == 'nan':
                params[key] = ''

            if key.endswith('date') and value != 'None' and value != 'nan':
                value = datetime.strptime(value, '%Y-%m-%d')
                params[key] = value.strftime('«%d» %B %Y года')
            elif key.endswith('date'):
                params[key] = '«__» ______ 20__ года'

        params['animalinshelter__aviary_number'] = params['animalinshelter__aviary_number'].split('.')[0]
        doc.render(params)

        return doc
