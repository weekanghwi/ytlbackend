from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import *

@receiver(post_save, sender=SiteBasicinfo)
def create_related_models(sender, instance, created, **kwargs):
  if created:
    material = Material.objects.create(sitebasicinfo=instance)
    do = DO.objects.create(sitebasicinfo=instance)
    install = Install.objects.create(sitebasicinfo=instance)
    ssv = SSV.objects.create(sitebasicinfo=instance)
    optimization = Optimization.objects.create(sitebasicinfo=instance)
    certification = Certification.objects.create(sitebasicinfo=instance)
    AllTable.objects.create(
      sitebasicinfo=instance,
      material=material,
      do=do,
      install=install,
      ssv=ssv,
      optimization=optimization,
      certification=certification
    )
  
# @receiver(post_save, sender=Material)
# def update_alltable_on_material(sender, instance, created, **kwargs):
#   try:
#     all_table = AllTable.objects.get(sitebasicinfo=instance.sitebasicinfo)
#     all_table.material = instance
#     all_table.save(update_fields=['material'])
#   except AllTable.DoesNotExist:
#     print('Alltable does not exist. Creating now.')
#     # AllTable.objects.create(sitebasicinfo=instance.sitebasicinfo, material=instance)

# @receiver(post_save, sender=DO)
# def update_alltable_on_do(sender, instance, created, **kwargs):
#   try:
#     all_table = AllTable.objects.get(sitebasicinfo=instance.sitebasicinfo)
#     all_table.do = instance
#     all_table.save(update_fields=['do'])
#   except AllTable.DoesNotExist:
#     print('Alltable does not exist. Creating now.')
#     # AllTable.objects.create(sitebasicinfo=instance.sitebasicinfo, do=instance)

# @receiver(post_save, sender=Install)
# def update_alltable_on_install(sender, instance, created, **kwargs):
#   try:
#     all_table = AllTable.objects.get(sitebasicinfo=instance.sitebasicinfo)
#     all_table.install = instance
#     all_table.save(update_fields=['install'])
#   except AllTable.DoesNotExist:
#     print('Alltable does not exist. Creating now.')
#     # AllTable.objects.create(sitebasicinfo=instance.sitebasicinfo, install=instance)

# @receiver(post_save, sender=SSV)
# def update_alltable_on_ssv(sender, instance, created, **kwargs):
#   try:
#     all_table = AllTable.objects.get(sitebasicinfo=instance.sitebasicinfo)
#     all_table.ssv = instance
#     all_table.save(update_fields=['ssv'])
#   except AllTable.DoesNotExist:
#     print('Alltable does not exist. Creating now.')
#     # AllTable.objects.create(sitebasicinfo=instance.sitebasicinfo, ssv=instance)

# @receiver(post_save, sender=Optimization)
# def update_alltable_on_optimization(sender, instance, created, **kwargs):
#   try:
#     all_table = AllTable.objects.get(sitebasicinfo=instance.sitebasicinfo)
#     all_table.optimization = instance
#     all_table.save(update_fields=['optimization'])
#   except AllTable.DoesNotExist:
#     print('Alltable does not exist. Creating now.')
#     # AllTable.objects.create(sitebasicinfo=instance.sitebasicinfo, optimization=instance)

# @receiver(post_save, sender=Certification)
# def update_alltable_on_certification(sender, instance, created, **kwargs):
#   try:
#     all_table = AllTable.objects.get(sitebasicinfo=instance.sitebasicinfo)
#     all_table.certification = instance
#     all_table.save(update_fields=['certification'])
#   except AllTable.DoesNotExist:
#     print('Alltable does not exist. Creating now.')
#     # AllTable.objects.create(sitebasicinfo=instance.sitebasicinfo, certification=instance)