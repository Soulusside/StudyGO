import datetime
import locale

from docxtpl import DocxTemplate

from django.db import models

from animals.models import AnimalInShelter


locale.setlocale(locale.LC_TIME, 'ru_RU.UTF-8')


class Company(models.Model):
    name = models.CharField(max_length=126)

    def __str__(self):
        return self.name


class Shelter(models.Model):
    name = models.CharField(max_length=126)
    address = models.CharField(max_length=126)
    company = models.CharField(max_length=126)
    telephone = models.CharField(max_length=31)
    leader = models.CharField(max_length=126)
    email = models.EmailField()

    def __str__(self):
        return f"{self.address} @{self.company}"

    def from_dict(row):
        shelter = Shelter.objects.filter(address=row['shelter__address']).first()
        if shelter is None:
            shelter = Shelter()

        company = Company.objects.filter(name=row['shelter__company']).first()
        if company is None:
            Company.objects.create(name=row['shelter__company'])

        shelter.address = row['shelter__address']
        shelter.company = row['shelter__company']
        shelter.leader = row['shelter__leader']
        shelter.save()

        return shelter

    def generate_report(self):
        doc = DocxTemplate('docx_templates/report_template.docx')
        context = {
            'address': self.address,
            'company': self.company,
            'today': datetime.datetime.now().strftime('«%d» %B %Y год'),
            'tbl_contents': [
                {'label': i+1, 'cols': [
                    ais.animal.cart_number,
                    ais.animal.name,
                    ais.animal.kind.name,
                    ais.animal.sex.name,
                    ais.animal.identification_number,
                    ais.arrived_date
                ]}
            for i, ais in enumerate(AnimalInShelter.objects.filter(shelter=self))]
        }

        doc.render(context)
        
        return doc


class ShelterStaff(models.Model):
    shelter = models.ForeignKey(Shelter, on_delete=models.CASCADE)
    name = models.CharField(max_length=31)

    def __str__(self):
        return self.name

    def from_dict(row):
        shelter = Shelter.from_dict(row)

        staff = ShelterStaff.objects.filter(
            shelter=shelter, name=row['animal_schelter__responsible']).first()

        if staff is None:
            staff = ShelterStaff()

        staff.shelter = shelter
        staff.name = row['animal_schelter__responsible']

        staff.save()

        return staff
