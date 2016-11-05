from __future__ import unicode_literals
from django.utils import timezone

from django.db import models

class Shopper(models.Model):
	'''
		Model for shopper 
	'''
	id = models.AutoField(serialize=False, primary_key=True)
	name = models.CharField(max_length=100)
	email = models.CharField(max_length=100, unique=True)
	phone = models.IntegerField(unique=True)
	city = models.CharField(max_length=100)
	state = models.CharField(max_length=100)
	application_date = models.DateField(db_index=True, default=timezone.now)
	workflow_state = models.CharField(max_length=100, default='applied')
	created_at = models.DateField(default=timezone.now)
	updated_at = models.DateField(default=timezone.now)

	def __str__(self):
		return '%s %s %s %s %s' % (self.id, self.name, self.email, self.phone, self.workflow_state)
