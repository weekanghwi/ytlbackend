from django.core.management.base import BaseCommand
import csv
from apiapp.models import Install

class Command(BaseCommand):
  help = 'Import data from CSV file into SiteBasicinfo model'

  def handle(self, *args, **options):
    # 파일 경로를 직접 지정
    csv_file_path = 'rawdata/install.csv'

    with open(csv_file_path, mode ='r') as file:
      csvFile = csv.DictReader(file)

      for lines in csvFile:
        sitebasicinfo = lines['sitebasicinfo']
        startdate = lines['startdate'] if lines['startdate'] else None
        completedate = lines['completedate'] if lines['completedate'] else None
        integrationdate = lines['integrationdate'] if lines['integrationdate'] else None
        integrationondate = lines['integrationondate'] if lines['integrationondate'] else None
        oaairdate = lines['oaairdate'] if lines['oaairdate'] else None
        coisubmitdate = lines['coisubmitdate'] if lines['coisubmitdate'] else None
        coiapprovedate = lines['coiapprovedate'] if lines['coiapprovedate'] else None
        coicsubmitdate = lines['coicsubmitdate'] if lines['coicsubmitdate'] else None
        coicapprovestatus = lines['coicapprovestatus'] if lines['coicapprovestatus'] else None
        pnochotriggerdate = lines['pnochotriggerdate'] if lines['pnochotriggerdate'] else None
        pnochocompletedate = lines['pnochocompletedate'] if lines['pnochocompletedate'] else None

        Install.objects.create(
          sitebasicinfo_id=sitebasicinfo,
          startdate=startdate,
          completedate=completedate,
          integrationdate=integrationdate,
          integrationondate=integrationondate,
          oaairdate=oaairdate,
          coisubmitdate=coisubmitdate,
          coiapprovedate=coiapprovedate,
          coicsubmitdate=coicsubmitdate,
          coicapprovestatus_id=coicapprovestatus,
          pnochotriggerdate=pnochotriggerdate,
          pnochocompletedate=pnochocompletedate
        )
    self.stdout.write(self.style.SUCCESS('Successfully imported the csv file into database'))
