# signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from base.models import Pet
from django.core.cache import cache
import logging

logger = logging.getLogger('base')

def updateUser(sender, instance, **kwargs):
    logger.info('Change User email to username')
    user = instance
    if user.email != '':
        user.username = user.email

@receiver(post_save, sender=Pet)
@receiver(post_delete, sender=Pet)
def clear_pet_cache(sender, instance, **kwargs):
    # Borra todas las claves de caché que comienzan con 'pets-'
    keys = cache.keys('pets-*')
    cache.delete_many(keys)
    logger.info('Cache de mascotas borrada.')
