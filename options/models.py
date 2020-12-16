from django.db import models


class AnimalKind(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalSex(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalBreed(models.Model):
    name = models.CharField(max_length=127)
    kind = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalColor(models.Model):
    name = models.CharField(max_length=127)
    kind = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalWool(models.Model):
    name = models.CharField(max_length=127)
    kind = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalEars(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalTail(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalDeathReason(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalLeaveReason(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name


class AnimalEuthanasiaReason(models.Model):
    name = models.CharField(max_length=127)

    def __str__(self):
        return self.name
