from django.core.management.base import BaseCommand
import csv
from apiapp.models import SitePhyinfo, SiteBasicinfo, Region, StatisticData
from django.db import connection

class Command(BaseCommand):
  help = 'Update or create data from CSV file into Site LSM info model'

  def handle(self, *args, **options):
    csv_file_path = 'rawdata/WEEK36_STATISTICDATA.csv'
    unique_ids_in_csv = []

    with open(csv_file_path, mode='r') as file:
      csvFile = csv.DictReader(file)
      
      processed_count = 0
      created_count = 0
      update_count = 0

      for lines in csvFile:
        processed_count += 1

        uid = lines['uid']
        region = lines['region'] if lines['region'] else None
        sitebasicinfo = lines['uid'].split('-')[0] if lines['uid'] else None
        cellnum = int(lines['cellnum']) if lines['cellnum'] else None

        # unique_id = f'{sitebasicinfo_id}-{cellnum}'
        unique_ids_in_csv.append(uid)

        phyinfo_instance = SitePhyinfo.objects.filter(uid=uid).first()
        sitebasicinfo_instance = SiteBasicinfo.objects.filter(siteid=sitebasicinfo).first()
        region_instance = Region.objects.filter(region__iexact=region).first()

        defaults = {
          'sitebasicinfo': sitebasicinfo_instance,
          'region': region_instance,
          'sitephyinfo': phyinfo_instance,
          'uid': uid,
          'sysid': lines['sys_id'] if lines['sys_id'] else None,
          'band': lines['band'] if lines['band'] else None,
          'year': int(lines['YEAR']) if lines['YEAR'] else None,
          'weeknum': lines['weeknum'] if lines['weeknum'] else None,
          'cluster': lines['cluster'] if lines['cluster'] else None,
          'cellnum': int(lines['cellnum']) if lines['cellnum'] else None,
          'cellunavailabletimedown': int(lines['sum(cellunavailabletimedown)']) if lines['sum(cellunavailabletimedown)'] else None,
          'cellunavailabletimelock': int(lines['sum(cellunavailabletimelock)']) if lines['sum(cellunavailabletimelock)'] else None,
          'cellavail_pmperiodtime': int(lines['sum(cellavail_pmperiodtime)']) if lines['sum(cellavail_pmperiodtime)'] else None,
          'connestabsucc': int(lines['sum(connestabsucc)']) if lines['sum(connestabsucc)'] else None,
          'connestabatt': int(lines['sum(connestabatt)']) if lines['sum(connestabatt)'] else None,
          's1connestabsucc': int(lines['sum(s1connestabsucc)']) if lines['sum(s1connestabsucc)'] else None,
          's1connestabatt': int(lines['sum(s1connestabatt)']) if lines['sum(s1connestabatt)'] else None,
          'establnitsuccnbr': int(lines['sum(establnitsuccnbr)']) if lines['sum(establnitsuccnbr)'] else None,
          'establnitattnbr': int(lines['sum(establnitattnbr)']) if lines['sum(establnitattnbr)'] else None,
          'establnitsuccnbr_qci59': int(lines['sum(establnitsuccnbr_qci59)']) if lines['sum(establnitsuccnbr_qci59)'] else None,
          'estabaddsuccnbr_qci59': int(lines['sum(estabaddsuccnbr_qci59)']) if lines['sum(estabaddsuccnbr_qci59)'] else None,
          'establnitattnbr_qci59': int(lines['sum(establnitattnbr_qci59)']) if lines['sum(establnitattnbr_qci59)'] else None,
          'estabaddattnbr_qci59': int(lines['sum(estabaddattnbr_qci59)']) if lines['sum(estabaddattnbr_qci59)'] else None,
          'establnitsuccnbr_qci1': int(lines['sum(establnitsuccnbr_qci1)']) if lines['sum(establnitsuccnbr_qci1)'] else None,
          'estabaddsuccnbr_qci1': int(lines['sum(estabaddsuccnbr_qci1)']) if lines['sum(estabaddsuccnbr_qci1)'] else None,
          'establnitattnbr_qci1': int(lines['sum(establnitattnbr_qci1)']) if lines['sum(establnitattnbr_qci1)'] else None,
          'estabaddattnbr_qci1': int(lines['sum(estabaddattnbr_qci1)']) if lines['sum(estabaddattnbr_qci1)'] else None,
          'calldropqci_eccbdspauditrlcmaccallrelease_qci59': int(lines['sum(calldropqci_eccbdspauditrlcmaccallrelease_qci59)']) if lines['sum(calldropqci_eccbdspauditrlcmaccallrelease_qci59)'] else None,
          'calldropqci_eccbrcvresetrequestfromecmb_qci59': int(lines['sum(calldropqci_eccbrcvresetrequestfromecmb_qci59)']) if lines['sum(calldropqci_eccbrcvresetrequestfromecmb_qci59)'] else None,
          'calldropqci_eccbrcvcellreleaseindfromecmb_qci59': int(lines['sum(calldropqci_eccbrcvcellreleaseindfromecmb_qci59)']) if lines['sum(calldropqci_eccbrcvcellreleaseindfromecmb_qci59)'] else None,
          'calldropqci_eccbradiolinkfailure_qci59': int(lines['sum(calldropqci_eccbradiolinkfailure_qci59)']) if lines['sum(calldropqci_eccbradiolinkfailure_qci59)'] else None,
          'calldropqci_eccbdspauditmaccallrelease_qci59': int(lines['sum(calldropqci_eccbdspauditmaccallrelease_qci59)']) if lines['sum(calldropqci_eccbdspauditmaccallrelease_qci59)'] else None,
          'calldropqci_eccbarqmaxretransmission_qci59': int(lines['sum(calldropqci_eccbarqmaxretransmission_qci59)']) if lines['sum(calldropqci_eccbarqmaxretransmission_qci59)'] else None,
          'calldropqci_eccbdspauditrlccallrelease_qci59': int(lines['sum(calldropqci_eccbdspauditrlccallrelease_qci59)']) if lines['sum(calldropqci_eccbdspauditrlccallrelease_qci59)'] else None,
          'calldropqci_eccbtmoutrrcconnectionreconfig_qci59': int(lines['sum(calldropqci_eccbtmoutrrcconnectionreconfig_qci59)']) if lines['sum(calldropqci_eccbtmoutrrcconnectionreconfig_qci59)'] else None,
          'calldropqci_eccbtmoutrrcconnectionrestablish_qci59': int(lines['sum(calldropqci_eccbtmoutrrcconnectionrestablish_qci59)']) if lines['sum(calldropqci_eccbtmoutrrcconnectionrestablish_qci59)'] else None,
          'calldropqci_eccbsisctpoutofsevice_qci59': int(lines['sum(calldropqci_eccbsisctpoutofsevice_qci59)']) if lines['sum(calldropqci_eccbsisctpoutofsevice_qci59)'] else None,
          'interx2insucc_qci59': int(lines['sum(interx2insucc_qci59)']) if lines['sum(interx2insucc_qci59)'] else None,
          'inters1insucc_qci59': int(lines['sum(inters1insucc_qci59)']) if lines['sum(inters1insucc_qci59)'] else None,
          'sumvoltecalldropqci': int(lines['sum(sumvoltecalldropqci)']) if lines['sum(sumvoltecalldropqci)'] else None,
          'sumvolteestablnitsuccnbr': int(lines['sum(sumvolteestablnitsuccnbr)']) if lines['sum(sumvolteestablnitsuccnbr)'] else None,
          'sumvolteestabaddsuccnbr': int(lines['sum(sumvolteestabaddsuccnbr)']) if lines['sum(sumvolteestabaddsuccnbr)'] else None,
          'sumvolteerablncominghosuccnbr': int(lines['sum(sumvolteerablncominghosuccnbr)']) if lines['sum(sumvolteerablncominghosuccnbr)'] else None,
          'intrafreqoutsucc': int(lines['sum(intrafreqoutsucc)']) if lines['sum(intrafreqoutsucc)'] else None,
          'intrafreqoutatt': int(lines['sum(intrafreqoutatt)']) if lines['sum(intrafreqoutatt)'] else None,
          'interfreqmeasgapoutsucc': int(lines['sum(interfreqmeasgapoutsucc)']) if lines['sum(interfreqmeasgapoutsucc)'] else None,
          'interfreqnomeasgapoutsucc': int(lines['sum(interfreqnomeasgapoutsucc)']) if lines['sum(interfreqnomeasgapoutsucc)'] else None,
          'interfreqmeasgapoutatt': int(lines['sum(interfreqmeasgapoutatt)']) if lines['sum(interfreqmeasgapoutatt)'] else None,
          'interfreqnomeasgapoutatt': int(lines['sum(interfreqnomeasgapoutatt)']) if lines['sum(interfreqnomeasgapoutatt)'] else None,
          'interx2outsucc': int(lines['sum(interx2outsucc)']) if lines['sum(interx2outsucc)'] else None,
          'interx2outatt': int(lines['sum(interx2outatt)']) if lines['sum(interx2outatt)'] else None,
          'interx2insucc': int(lines['sum(interx2insucc)']) if lines['sum(interx2insucc)'] else None,
          'interx2inatt': int(lines['sum(interx2inatt)']) if lines['sum(interx2inatt)'] else None,
          'inters1outsucc': int(lines['sum(inters1outsucc)']) if lines['sum(inters1outsucc)'] else None,
          'inters1outatt': int(lines['sum(inters1outatt)']) if lines['sum(inters1outatt)'] else None,
          'inters1insucc': int(lines['sum(inters1insucc)']) if lines['sum(inters1insucc)'] else None,
          'inters1inatt': int(lines['sum(inters1inatt)']) if lines['sum(inters1inatt)'] else None,
          'dltransmissionnackedretrans': int(lines['sum(dltransmissionnackedretrans)']) if lines['sum(dltransmissionnackedretrans)'] else None,
          'dltransmissionretrans0_600': int(lines['sum(dltransmissionretrans0_600)']) if lines['sum(dltransmissionretrans0_600)'] else None,
          'ultransmissionnackedretrans': int(lines['sum(ultransmissionnackedretrans)']) if lines['sum(ultransmissionnackedretrans)'] else None,
          'ultransmissionretrans0_600': int(lines['sum(ultransmissionretrans0_600)']) if lines['sum(ultransmissionretrans0_600)'] else None,
          'connectno': float(lines['AVG(connno)']) if lines['AVG(connno)'] else None,
          'connectmax': float(lines['AVG(connmax)']) if lines['AVG(connmax)'] else None,
          'totalprbdl': float(lines['AVG(totalprbdl)']) if lines['AVG(totalprbdl)'] else None,
          'totalprbul': float(lines['AVG(totalprbul)']) if lines['AVG(totalprbul)'] else None,
        }

        obj, created = StatisticData.objects.update_or_create(
          uid=uid,
          cellnum=cellnum,
          defaults=defaults
        )

        if created:
          created_count += 1
          self.stdout.write(f'Created new record for {uid}')
        else:
          update_count += 1
          self.stdout.write(f'Updated existing record for {uid}')
        self.stdout.write(f'Processed {processed_count} rows so far')

      all_site_lsm_info = StatisticData.objects.all()

      for site_info in all_site_lsm_info:
        unique_id_db = site_info.uid
        if unique_id_db not in unique_ids_in_csv:
          site_info.sitestatus = 'Dismantled'
          site_info.save()

          self.stdout.write(f'Updated remark to dismantled for {unique_id_db}')
    self.stdout.write(self.style.SUCCESS('Successfully updated the database with CSV file'))