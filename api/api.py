import random
import string
import base64
import datetime

import requests

from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from django.http         import JsonResponse
from django.core.files.base import ContentFile
from django.shortcuts    import render

from animals.models import *
from options.models import *
from shelter.models import *


class Route:
    @csrf_exempt
    def route(request):
        route = Route()

        print(request.method)
        handle = getattr(route, "do_" + request.method)

        try:
            return handle(request)

        except Exception as e:
            print("EXCEPTION:", e)
            return route.raise_error(-1)

    def do_GET(self, request):
        section = request.GET.get('section', None)
        method  = request.GET.get('method',  None)
        params  = request.GET.get('params',  None)

        if section == None and method == None or params == None:
            return self.raise_error(1)

        attr = section + "_" + method

        if not hasattr(self, attr):
            print(hasattr(self, attr), attr)
            return self.raise_error(9)

        handle = getattr(self, attr)
        print('params:', params)

        return handle(eval(params))

    def do_POST(self, request):
        section = request.POST.get('section', None)
        method  = request.POST.get('method',  None)
        params  = request.POST.get('params',  None)

        if section == None and method == None or params == None:
            return self.raise_error(1)

        attr = section + "_" + method

        if not hasattr(self, attr):
            return self.raise_error(9)

        handle = getattr(self, attr)

        return handle(eval(params))

    def animal_filter(self, params):
        animals = Animal.filter_by_params(params, is_socialization=True)
        result = self.generate_result_objects(animals, 'animals',
            fields=['id', 'name', 'breed_id', 'sex_id', 'age', 'cart_number'])

        return self.json_response(result)

    def animal_get_animal(self, params):
        animal_id = params['animal_id']

        animal = Animal.objects.filter(id=animal_id, is_socialization=True).first()
        if animal is None:
            return self.raise_error(2)

        if not animal.current_shelter.leave_reason is None:
            return self.raise_error(3)

        result = self.generate_result_one_object(animal, fields=['id', 'name',
            'breed_id', 'wool_id', 'size_name', 'age', 'ears_id', 'color_id',
            'cart_number', 'kind_id', 'sex_id', 'special_signs', 'sterialization_status',
            'sterialization_veterinarian_name', 'tail_id', 'weight',
            'current_shelter_name', 'current_shelter_address', 'current_shelter_email'])

        return self.json_response(result)

    def shelter_get_shelters(self, params):
        shelters = Shelter.objects.all()
        result = self.generate_result_objects(shelters, 'shelters')

        return self.json_response(result)

    def shelter_request(self, params):
        animal_id = params['animal_id']

        animal = Animal.objects.filter(id=animal_id).first()
        if animal is None:
            return self.raise_error(2)

        ais = animal.current_shelter
        if ais is None:
            return self.raise_error(1)

        animal_request = AnimalRequest.create_request(
            ais, params['owner_name'],params['owner_contact'])

        result = self.generate_result_by_key_value('request_id', animal_request.id)

        return self.json_response(result)

    def shelter_leave_animal(self, params):
        def add_suffix_to_params(suffix):
            d = {}

            for key in params:
                d[f'{suffix}__{key}'] = params[key]

            return d

        animal_id = params['animal_id']
        leave_act = params['leave_act']
        leave_reason = params['leave_reason']

        animal = Animal.objects.filter(id=animal_id).first()
        if animal is None:
            return self.raise_error(2)

        animal_current_shelter = animal.current_shelter
        animal_current_shelter.leave_act = leave_act
        animal_current_shelter.leave_reason = AnimalLeaveReason.objects.get(id=leave_reason)
        animal_current_shelter.leave_date = datetime.now()
        animal_current_shelter.save()

        if leave_reason == 1:
            return self.json_response()

        if params['is_entity']:
            owner = OwnerEntity.from_dict(add_suffix_to_params('owner_entity'))
            animal.owner_entity = owner
        else:
            owner = OwnerIndividual.from_dict(add_suffix_to_params('owner_individual'))
            animal.owner_individual = owner

        animal.save()

        return self.json_response()

    def generate_result_one_object(self, object, fields=None):
        result = {}

        if fields is None:
            fields = object.__dict__

        for attr_name in fields:
            if attr_name[0] != "_":
                data, attr_name = self.get_object_attr(object, attr_name)

                result[attr_name] = data

        return dict([( type(object).__name__.lower(), result )])

    def get_object_attr(self, object, attr_name):
        data = getattr(object, attr_name)

        if attr_name.endswith('_id') and hasattr(object, attr_name[:-3]):
            attr_name = attr_name[:-3]

            if hasattr(getattr(object, attr_name), 'name'):
                data = getattr(getattr(object, attr_name), 'name')

        if type(data).__name__ == "method":
            data = data()
        elif type(data).__name__ == "ImageFieldFile":
            data = data.url
        elif type(data).__name__ == "datetime":
            data = str(data.now())

        return data, attr_name

    def generate_result_objects(self, objects, name, fields=None):
        result = []

        for object in objects:
            data = self.generate_result_one_object(object, fields=fields)
            result.append(data[type(object).__name__.lower()])

        return {
            'data': result,
            'count': len(result)
        }

    def generate_result_by_key_value(self, key, value):
        return {
            key: value,
        }

    def json_response(self, result=[], error_code=0):

        return JsonResponse({
            "result": result,
            "error_code": error_code,
            "error_text": self.ERRORS[error_code],
        })

    def raise_error(self, error_code, text=None):
        error_text =  self.ERRORS[error_code] if text is None else text

        return JsonResponse(
            {
                "result" : [],
                "error_code": error_code,
                "error_text": error_text
            }
        )

    ERRORS = {
        -1: 'Неожиданная ошибка.',
        0:  'Успешно!',
        1:  'Необходимые параметры отсутствуют',
        2:  'Социализированного животного с таким id нет',
        3:  'Животное уже не в приюте',
        4:  'Нет поля: point',
        5:  'Неизвестная инициатива',
        6:  'Неправльный логин или пароль',
        7:  'Пользователь с таким телефоном уже существует',
        8:  'Неправльный код',
        9:  'Section или method не сущесвует',
        10: 'ф',
        11: 'Неизвестный section',
        12: 'Повторное голосование невозможно'
    }
