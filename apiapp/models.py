# from django.db import models
from django.contrib.gis.db import models
from django.contrib.gis.geos import Point
from django.utils import timezone
from django.core.exceptions import ObjectDoesNotExist
from django.conf import settings
from apiapp.middleware import get_current_user

#--------------------------------------------------------------------------------------------------
#Common Table--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class Subcon(models.Model):
  subcon = models.CharField(max_length=100)
  type = models.CharField(max_length=50)
  remark = models.TextField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.subcon

#--------------------------------------------------------------------------------------------------
#Related Basesiteinfo------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class ContractType(models.Model):
  contracttype = models.CharField(max_length=20, unique=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.contracttype

class Region(models.Model):
  region = models.CharField(max_length=10, unique=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.region

class State(models.Model):
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  state = models.CharField(max_length=30, unique=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.state

class Cluster(models.Model):
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  cluster = models.CharField(max_length=100, unique=True)
  polygon = models.PolygonField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.cluster

class SiteConfig(models.Model):
  siteconfig = models.CharField(max_length=20, unique=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.siteconfig

class SiteBasicinfo(models.Model):
  siteid = models.CharField(max_length=15, unique=True)
  sitename = models.CharField(max_length=100)
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True )
  state = models.ForeignKey(State, on_delete=models.CASCADE, null=True)
  lat = models.DecimalField(max_digits=30, decimal_places=20, null=True, blank=True)
  lon = models.DecimalField(max_digits=30, decimal_places=20, null=True, blank=True)
  point = models.PointField(null=True, blank=True)
  cluster = models.ForeignKey(Cluster, on_delete=models.CASCADE, null=True)
  contracttype = models.ForeignKey(ContractType, on_delete=models.CASCADE, null=True)
  siteconfig = models.ForeignKey(SiteConfig, on_delete=models.CASCADE, null=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def save(self, *args, **kwargs):
    if self.lat and self.lon:
      try:
        self.point = Point(float(self.lon), float(self.lat))
      except ValueError:
        self.point = None
    else:
      self.point = None
    super(SiteBasicinfo, self).save(*args, **kwargs)
  def __str__(self):
    return self.siteid

#--------------------------------------------------------------------------------------------------
#SitePhyinfo---------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class AntennaType(models.Model):
  antennatype = models.CharField(max_length=20, unique=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.antennatype

class SitePhyinfo(models.Model):
  uid = models.CharField(max_length=20, blank=True, editable=False)
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  secid = models.IntegerField(null=True, blank=True)
  portnum = models.IntegerField(null=True, blank=True)
  band = models.IntegerField(null=True, blank=True)
  antennatype = models.ForeignKey(AntennaType, on_delete=models.CASCADE, null=True)
  antennaheight = models.IntegerField(null=True, blank=True)
  azimuth = models.IntegerField(null=True, blank=True)
  mtilt = models.IntegerField(null=True, blank=True)
  etilt = models.IntegerField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  modified_by = models.CharField(max_length=50, null=True, blank=True)
  def save(self, *args, **kwargs):
    self.uid = f'{self.sitebasicinfo.siteid}-{self.portnum}'
    super(SitePhyinfo, self).save(*args, **kwargs)
  def __str__(self):
    return str(self.sitebasicinfo.siteid)

#--------------------------------------------------------------------------------------------------
#Site LSM Info-------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SiteLSMinfo(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  uid = models.CharField(max_length=20, blank=True, editable=False)
  siteid = models.CharField(max_length=15, null=True, blank=True)
  cellnum = models.IntegerField(null=True, blank=True)
  cellidentity = models.IntegerField(null=True, blank=True)
  pci = models.IntegerField(null=True, blank=True)
  pss = models.IntegerField(editable=False)
  sss = models.IntegerField(editable=False)
  earfcndl = models.IntegerField(null=True, blank=True)
  earfcnul = models.IntegerField(null=True, blank=True)
  freqband = models.IntegerField(null=True, blank=True)
  rsi = models.IntegerField(null=True, blank=True)
  tac = models.IntegerField(null=True, blank=True)
  channelcard = models.CharField(max_length=15, null=True, blank=True)
  sitestatus = models.CharField(max_length=50, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def save(self, *args, **kwargs):
    self.uid = f'{self.siteid}-{self.cellnum}'
    self.pss = self.pci % 3
    self.sss = (self.pci - (self.pci % 3)) / 3
    super(SiteLSMinfo, self).save(*args, **kwargs)
  
  def __str__(self):
    return str(self.uid) 

#--------------------------------------------------------------------------------------------------
#Site RET info-------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class ReferenceRET(models.Model):
  uid = models.CharField(max_length=50, unique=True)
  band = models.CharField(max_length=20, null=True, blank=True)
  secid = models.IntegerField(null=True, blank=True)
  portnum = models.IntegerField(null=True, blank=True)
  channelcard = models.CharField(max_length=50, null=True, blank=True)
  antennatype = models.CharField(max_length=50, null=True, blank=True)
  remark = models.CharField(max_length=50, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.uid)

class SiteRETinfo(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  uid = models.CharField(max_length=20, blank=True, editable=False)
  siteid = models.CharField(max_length=15, blank=True, editable=False)
  connectboardtype = models.IntegerField(null=True, blank=True)
  connectboardid = models.IntegerField(null=True, blank=True)
  connectportid = models.IntegerField(null=True, blank=True)
  cascaderrhid = models.IntegerField(null=True, blank=True)
  aldid = models.IntegerField(null=True, blank=True)
  antidsubnetid = models.IntegerField(null=True, blank=True)
  tilt = models.IntegerField(null=True, blank=True)

  refuid = models.CharField(max_length=100, editable=False, null=True, blank=True)
  channelcard = models.CharField(max_length=15, editable=False, null=True, blank=True)
  band = models.CharField(max_length=20, editable=False, null=True, blank=True)
  secid = models.IntegerField(editable=False, null=True, blank=True)
  portnum = models.IntegerField(editable=False, null=True, blank=True)
  antennatype = models.CharField(max_length=50, editable=False, null=True, blank=True)

  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)

  def save(self, *args, **kwargs):
    lsm_info = SiteLSMinfo.objects.filter(siteid=self.siteid).first()
    phy_info = SitePhyinfo.objects.filter(sitebasicinfo__siteid=self.siteid).first()

    if lsm_info and lsm_info.channelcard:
      self.channelcard = lsm_info.channelcard

    if phy_info and phy_info.antennatype:
       self.antennatype = phy_info.antennatype

    if lsm_info and phy_info:
      if phy_info.antennatype.antennatype == '10T10R':
        self.refuid = f'{self.channelcard}-{self.connectboardid}-{self.connectportid}-{self.aldid}-{self.antidsubnetid}-{self.antennatype}'
      else:
        self.refuid = f'{self.channelcard}-{self.connectboardid}-{self.connectportid}-{self.aldid}-{self.antidsubnetid}-NORMAL'

      retreference_info = ReferenceRET.objects.filter(uid=self.refuid).first()
      if retreference_info:
        self.band = retreference_info.band
        self.secid = retreference_info.secid
        self.portnum = retreference_info.portnum
        self.uid = f'{self.siteid}-{self.portnum}'

    super(SiteRETinfo, self).save(*args, **kwargs)

    
  def __str__(self):
    return str(self.uid)
  
#--------------------------------------------------------------------------------------------------
#Site TX Info--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SiteTXattninfo(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  uid = models.CharField(max_length=20, blank=True, editable=False)
  siteid = models.CharField(max_length=15, blank=True, editable=False)
  connectboardid = models.IntegerField(null=True, blank=True)
  connectportid = models.IntegerField(null=True, blank=True)
  txattn = models.IntegerField(null=True, blank=True)
  cellnum = models.IntegerField(null=True, blank=True)
  sitestatus = models.CharField(max_length=50, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def save(self, *args, **kwargs):
    self.uid = f'{self.siteid}-{self.cellnum}'
    super(SiteTXattninfo, self).save(*args, **kwargs)
  
  def __str__(self):
    return str(self.uid)

#--------------------------------------------------------------------------------------------------
#Material------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class Material(models.Model):
  MATERIAL_CHOICES = [
    (None, 'None'),
    ('Samsung-Material', 'Samsung-Material'),
    ('Reuse-Material', 'Reuse-Material')
  ]
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  dumaterial = models.CharField(max_length=20, choices=MATERIAL_CHOICES, null=True)
  rumaterial = models.CharField(max_length=20, choices=MATERIAL_CHOICES, null=True)
  remark = models.TextField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid) 
#--------------------------------------------------------------------------------------------------
#DO INFO-------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class DO(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  doissuedate = models.DateField(null=True, blank=True)
  codsubmitdate = models.DateField(null=True, blank=True)
  codapprovedate = models.DateField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid) 

#--------------------------------------------------------------------------------------------------
#Install INFO--------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class COICApproveStatus(models.Model):
  coicapprovestatus = models.CharField(max_length=20)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.coicapprovestatus)

class Install(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  startdate = models.DateField(null=True, blank=True)
  completedate = models.DateField(null=True, blank=True)
  integrationdate = models.DateField(null=True, blank=True)
  integrationondate = models.DateField(null=True, blank=True)
  oaairdate = models.DateField(null=True, blank=True)
  coisubmitdate = models.DateField(null=True, blank=True)
  coiapprovedate = models.DateField(null=True, blank=True)
  coicsubmitdate = models.DateField(null=True, blank=True)
  coicapprovestatus = models.ForeignKey(COICApproveStatus, on_delete=models.CASCADE, null=True)
  pnochotriggerdate = models.DateField(null=True, blank=True)
  pnochocompletedate = models.DateField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid) 

#--------------------------------------------------------------------------------------------------
#SSV INFO------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class SSVIssuetype(models.Model):
  ssvissuetype = models.CharField(max_length=20, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.ssvissuetype) 

class SSV(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  ssvstartdate = models.DateField(null=True, blank=True)
  ssvcompletedate = models.DateField(null=True, blank=True)
  ssvsubmitdate = models.DateField(null=True, blank=True)
  bsreceivedate = models.DateField(null=True, blank=True)
  bssubmitdate = models.DateField(null=True, blank=True)
  bsapprovedate = models.DateField(null=True, blank=True)
  ssvsubcon = models.ForeignKey(Subcon, on_delete=models.CASCADE, null=True)
  ssvissuetype = models.ForeignKey(SSVIssuetype, on_delete=models.CASCADE, null=True)
  ssvissuedetail = models.TextField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid) 

#--------------------------------------------------------------------------------------------------
#OPT INFO------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class OPTType(models.Model):
  opttype = models.CharField(max_length=20)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.opttype) 

class OPTIssuetype(models.Model):
  optissuetype = models.CharField(max_length=20, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.optissuetype)
  
class PIC(models.Model):
  pic = models.CharField(max_length=50, null=True, blank=True)
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.pic) 

class ReviewStatus(models.Model):
  reviewstatus = models.CharField(max_length=50, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.reviewstatus)
  
class OptReview(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  reviewdate = models.DateField(null=True, blank=True)
  pic = models.ForeignKey(PIC, on_delete=models.CASCADE, null=True)
  reviewstatus = models.ForeignKey(ReviewStatus, on_delete=models.CASCADE, null=True)
  reviewdetail = models.TextField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid) 


class Optimization(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  opttype = models.ForeignKey(OPTType, on_delete=models.CASCADE, null=True)
  optstartdate = models.DateField(null=True, blank=True)
  optcompletedate = models.DateField(null=True, blank=True)
  optsubmitdate = models.DateField(null=True, blank=True)
  optapprovedate = models.DateField(null=True, blank=True)
  optsubcon = models.ForeignKey(Subcon, on_delete=models.CASCADE, null=True)
  optissuetype = models.ForeignKey(OPTIssuetype, on_delete=models.CASCADE, null=True)
  optissuedetail = models.TextField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.name) 

#--------------------------------------------------------------------------------------------------
#Certi INFO----------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class PACApproveStatus(models.Model):
  pacapprovestatus = models.CharField(max_length=50)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.pacapprovestatus

class FACApproveStatus(models.Model):
  facapprovestatus = models.CharField(max_length=50)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return self.facapprovestatus

class Certification(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  pacsubmitdate = models.DateField(null=True, blank=True)
  facsubmitdate = models.DateField(null=True, blank=True)
  pacapprovestatus = models.ForeignKey(PACApproveStatus, on_delete=models.CASCADE, null=True)
  facapprovestatus = models.ForeignKey(FACApproveStatus, on_delete=models.CASCADE, null=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid) 

#--------------------------------------------------------------------------------------------------
#Table sum-----------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class AllTable(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  material = models.ForeignKey(Material, on_delete=models.CASCADE, null=True)
  do = models.ForeignKey(DO, on_delete=models.CASCADE, null=True)
  install = models.ForeignKey(Install, on_delete=models.CASCADE, null=True)
  ssv = models.ForeignKey(SSV, on_delete=models.CASCADE, null=True)
  optimization = models.ForeignKey(Optimization, on_delete=models.CASCADE, null=True)
  certification = models.ForeignKey(Certification, on_delete=models.CASCADE, null=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid)
  
#--------------------------------------------------------------------------------------------------
#TEST RESULT (POOR SINR)---------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class TestResult(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  cycle = models.CharField(null=True, blank=True)
  testdata = models.FileField(upload_to='test_results/')
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid)
  
#--------------------------------------------------------------------------------------------------
#Statistic-----------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------
class Statistic(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  band = models.CharField(max_length=100, null=True, blank=True)
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  cluster = models.CharField(max_length=100, null=True, blank=True)
  sysid = models.CharField(max_length=50, null=True, blank=True)
  cellnum = models.IntegerField(null=True, blank=True)
  year = models.IntegerField(null=True, blank=True)
  weeknum = models.CharField(max_length=50, null=True, blank=True)
  uid = models.CharField(max_length=100, null=True, blank=True)
  sitephyinfo = models.ForeignKey(SitePhyinfo, on_delete=models.CASCADE, null=True)
  cell_availability = models.FloatField(null=True, blank=True)
  attach_setup_success_rate = models.FloatField(null=True, blank=True)
  rrc_setup_success_rate = models.FloatField(null=True, blank=True)
  erab_setup_success_rate_ngbr = models.FloatField(null=True, blank=True)
  volte_setup_success_rate_gbr = models.FloatField(null=True, blank=True)
  call_drop_rate_erab_ngbr = models.FloatField(null=True, blank=True)
  volte_call_drop_rate_erab_gbr = models.FloatField(null=True, blank=True)
  hosr_intra_frequency = models.FloatField(null=True, blank=True)
  hosr_inter_frequency = models.FloatField(null=True, blank=True)
  x2_handover_out_success_rate = models.FloatField(null=True, blank=True)
  x2_handover_in_success_rate = models.FloatField(null=True, blank=True)
  s1_handover_out_success_rate = models.FloatField(null=True, blank=True)
  s1_handover_in_success_rate = models.FloatField(null=True, blank=True)
  dl_bler = models.FloatField(null=True, blank=True)
  ul_bler = models.FloatField(null=True, blank=True)
  sitestatus = models.CharField(max_length=100, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid)

#Statistic DATA------------------------------------------------------------------------------------
class StatisticData(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  band = models.CharField(max_length=100, null=True, blank=True)
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  cluster = models.CharField(max_length=100, null=True, blank=True)
  sysid = models.CharField(max_length=50, null=True, blank=True)
  cellnum = models.IntegerField(null=True, blank=True)
  year = models.IntegerField(null=True, blank=True)
  weeknum = models.CharField(max_length=50, null=True, blank=True)
  uid = models.CharField(max_length=100, null=True, blank=True)
  sitephyinfo = models.ForeignKey(SitePhyinfo, on_delete=models.CASCADE, null=True)
  cellunavailabletimedown = models.IntegerField(null=True, blank=True)
  cellunavailabletimelock = models.IntegerField(null=True, blank=True)
  cellavail_pmperiodtime = models.IntegerField(null=True, blank=True)
  connestabsucc = models.IntegerField(null=True, blank=True)
  connestabatt = models.IntegerField(null=True, blank=True)
  s1connestabsucc = models.IntegerField(null=True, blank=True)
  s1connestabatt = models.IntegerField(null=True, blank=True)
  establnitsuccnbr = models.IntegerField(null=True, blank=True)
  establnitattnbr = models.IntegerField(null=True, blank=True)
  establnitsuccnbr_qci59 = models.IntegerField(null=True, blank=True)
  estabaddsuccnbr_qci59 = models.IntegerField(null=True, blank=True)
  establnitattnbr_qci59 = models.IntegerField(null=True, blank=True)
  estabaddattnbr_qci59 = models.IntegerField(null=True, blank=True)
  establnitsuccnbr_qci1 = models.IntegerField(null=True, blank=True)
  estabaddsuccnbr_qci1 = models.IntegerField(null=True, blank=True)
  establnitattnbr_qci1 = models.IntegerField(null=True, blank=True)
  estabaddattnbr_qci1 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbdspauditrlcmaccallrelease_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbrcvresetrequestfromecmb_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbrcvcellreleaseindfromecmb_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbradiolinkfailure_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbdspauditmaccallrelease_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbarqmaxretransmission_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbdspauditrlccallrelease_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbtmoutrrcconnectionreconfig_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbtmoutrrcconnectionrestablish_qci59 = models.IntegerField(null=True, blank=True)
  calldropqci_eccbsisctpoutofsevice_qci59 = models.IntegerField(null=True, blank=True)
  interx2insucc_qci59 = models.IntegerField(null=True, blank=True)
  inters1insucc_qci59 = models.IntegerField(null=True, blank=True)
  sumvoltecalldropqci = models.IntegerField(null=True, blank=True)
  sumvolteestablnitsuccnbr = models.IntegerField(null=True, blank=True)
  sumvolteestabaddsuccnbr = models.IntegerField(null=True, blank=True)
  sumvolteerablncominghosuccnbr = models.IntegerField(null=True, blank=True)
  intrafreqoutsucc = models.IntegerField(null=True, blank=True)
  intrafreqoutatt = models.IntegerField(null=True, blank=True)
  interfreqmeasgapoutsucc = models.IntegerField(null=True, blank=True)
  interfreqnomeasgapoutsucc = models.IntegerField(null=True, blank=True)
  interfreqmeasgapoutatt = models.IntegerField(null=True, blank=True)
  interfreqnomeasgapoutatt = models.IntegerField(null=True, blank=True)
  interx2outsucc = models.IntegerField(null=True, blank=True)
  interx2outatt = models.IntegerField(null=True, blank=True)
  interx2insucc = models.IntegerField(null=True, blank=True)
  interx2inatt = models.IntegerField(null=True, blank=True)
  inters1outsucc = models.IntegerField(null=True, blank=True)
  inters1outatt = models.IntegerField(null=True, blank=True)
  inters1insucc = models.IntegerField(null=True, blank=True)
  inters1inatt = models.IntegerField(null=True, blank=True)
  dltransmissionnackedretrans = models.IntegerField(null=True, blank=True)
  dltransmissionretrans0_600 = models.BigIntegerField(null=True, blank=True)
  ultransmissionnackedretrans = models.IntegerField(null=True, blank=True)
  ultransmissionretrans0_600 = models.BigIntegerField(null=True, blank=True)
  connectno = models.IntegerField(null=True, blank=True)
  connectmax = models.IntegerField(null=True, blank=True)
  totalprbdl = models.IntegerField(null=True, blank=True)
  totalprbul = models.IntegerField(null=True, blank=True)
  sitestatus = models.CharField(max_length=100, null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)
  def __str__(self):
    return str(self.sitebasicinfo.siteid)
  
class StatisticCalculated(models.Model):
  uid = models.CharField(max_length=100, null=True, blank=True)
  category = models.CharField(max_length=100, null=True, blank=True)
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  band = models.CharField(max_length=100, null=True, blank=True)
  weeknum = models.CharField(max_length=50, null=True, blank=True)
  cell_availability = models.FloatField(null=True, blank=True)
  attach_setup_success_rate = models.FloatField(null=True, blank=True)
  rrc_setup_success_rate = models.FloatField(null=True, blank=True)
  erab_setup_success_rate_ngbr = models.FloatField(null=True, blank=True)
  volte_setup_success_rate_gbr = models.FloatField(null=True, blank=True)
  call_drop_rate_erab_ngbr = models.FloatField(null=True, blank=True)
  volte_call_drop_rate_erab_gbr = models.FloatField(null=True, blank=True)
  hosr_intra_frequency = models.FloatField(null=True, blank=True)
  hosr_inter_frequency = models.FloatField(null=True, blank=True)
  x2_handover_out_success_rate = models.FloatField(null=True, blank=True)
  x2_handover_in_success_rate = models.FloatField(null=True, blank=True)
  s1_handover_out_success_rate = models.FloatField(null=True, blank=True)
  s1_handover_in_success_rate = models.FloatField(null=True, blank=True)
  dl_bler = models.FloatField(null=True, blank=True)
  ul_bler = models.FloatField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)

class StatisticCalculatedCluster(models.Model):
  uid = models.CharField(max_length=100, null=True, blank=True)
  region = models.ForeignKey(Region, on_delete=models.CASCADE, null=True)
  cluster = models.CharField(max_length=100, null=True, blank=True)
  band = models.CharField(max_length=100, null=True, blank=True)
  weeknum = models.CharField(max_length=50, null=True, blank=True)
  cell_availability = models.FloatField(null=True, blank=True)
  attach_setup_success_rate = models.FloatField(null=True, blank=True)
  rrc_setup_success_rate = models.FloatField(null=True, blank=True)
  erab_setup_success_rate_ngbr = models.FloatField(null=True, blank=True)
  volte_setup_success_rate_gbr = models.FloatField(null=True, blank=True)
  call_drop_rate_erab_ngbr = models.FloatField(null=True, blank=True)
  volte_call_drop_rate_erab_gbr = models.FloatField(null=True, blank=True)
  hosr_intra_frequency = models.FloatField(null=True, blank=True)
  hosr_inter_frequency = models.FloatField(null=True, blank=True)
  x2_handover_out_success_rate = models.FloatField(null=True, blank=True)
  x2_handover_in_success_rate = models.FloatField(null=True, blank=True)
  s1_handover_out_success_rate = models.FloatField(null=True, blank=True)
  s1_handover_in_success_rate = models.FloatField(null=True, blank=True)
  dl_bler = models.FloatField(null=True, blank=True)
  ul_bler = models.FloatField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)
  modify_at = models.DateTimeField(auto_now=True)

class AlarmData(models.Model):
  sitebasicinfo = models.ForeignKey(SiteBasicinfo, on_delete=models.CASCADE, null=True)
  site_name = models.CharField(max_length=100, null=True, blank=True)
  folder = models.CharField(max_length=100, null=True, blank=True)
  alarm = models.TextField(null=True, blank=True)
  material_remark = models.CharField(max_length=100, null=True, blank=True)
  alarmdate = models.DateField(null=True, blank=True)
  create_at = models.DateTimeField(default=timezone.now)

  def __str__(self):
    return str(self.sitebasicinfo.siteid)