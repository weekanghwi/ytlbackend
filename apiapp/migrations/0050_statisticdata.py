# Generated by Django 4.2.4 on 2023-11-03 03:04

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0049_rename_rrd_setup_success_rate_statistic_rrc_setup_success_rate'),
    ]

    operations = [
        migrations.CreateModel(
            name='StatisticData',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('band', models.CharField(blank=True, max_length=100, null=True)),
                ('cluster', models.CharField(blank=True, max_length=100, null=True)),
                ('sysid', models.CharField(blank=True, max_length=50, null=True)),
                ('cellnum', models.IntegerField(blank=True, null=True)),
                ('year', models.IntegerField(blank=True, null=True)),
                ('weeknum', models.CharField(blank=True, max_length=50, null=True)),
                ('uid', models.CharField(blank=True, max_length=100, null=True)),
                ('cellunavailabletimedown', models.IntegerField(blank=True, null=True)),
                ('cellunavailabletimelock', models.IntegerField(blank=True, null=True)),
                ('cellavail_pmperiodtime', models.IntegerField(blank=True, null=True)),
                ('connestabsucc', models.IntegerField(blank=True, null=True)),
                ('connestabatt', models.IntegerField(blank=True, null=True)),
                ('s1connestabsucc', models.IntegerField(blank=True, null=True)),
                ('s1connestabatt', models.IntegerField(blank=True, null=True)),
                ('establnitsuccnbr', models.IntegerField(blank=True, null=True)),
                ('establnitattnbr', models.IntegerField(blank=True, null=True)),
                ('establnitsuccnbr_qci59', models.IntegerField(blank=True, null=True)),
                ('estabaddsuccnbr_qci59', models.IntegerField(blank=True, null=True)),
                ('establnitattnbr_qci59', models.IntegerField(blank=True, null=True)),
                ('estabaddattnbr_qci59', models.IntegerField(blank=True, null=True)),
                ('establnitsuccnbr_qci1', models.IntegerField(blank=True, null=True)),
                ('estabaddsuccnbr_qci1', models.IntegerField(blank=True, null=True)),
                ('establnitattnbr_qci1', models.IntegerField(blank=True, null=True)),
                ('estabaddattnbr_qci1', models.IntegerField(blank=True, null=True)),
                ('eccbdspauditrlcmaccallrelease_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbrcvresetrequestfromecmb_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbrcvcellreleaseindfromecmb_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbradiolinkfailure_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbdspauditmaccallrelease_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbarqmaxretransmission_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbdspauditrlccallrelease_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbtmoutrrcconnectionreconfig_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbtmoutrrcconnectionrestablish_qci59', models.IntegerField(blank=True, null=True)),
                ('calldropqci_eccbsisctpoutofsevice_qci59', models.IntegerField(blank=True, null=True)),
                ('interx2insucc_qci59', models.IntegerField(blank=True, null=True)),
                ('inters1insucc_qci59', models.IntegerField(blank=True, null=True)),
                ('sumvoltecalldropqci', models.IntegerField(blank=True, null=True)),
                ('sumvolteestablnitsuccnbr', models.IntegerField(blank=True, null=True)),
                ('sumvolteestabaddsuccnbr', models.IntegerField(blank=True, null=True)),
                ('sumvolteerablncominghosuccnbr', models.IntegerField(blank=True, null=True)),
                ('intrafreqoutsucc', models.IntegerField(blank=True, null=True)),
                ('intrafreqoutatt', models.IntegerField(blank=True, null=True)),
                ('interfreqmeasgapoutsucc', models.IntegerField(blank=True, null=True)),
                ('interfreqnomeasgapoutsucc', models.IntegerField(blank=True, null=True)),
                ('interfreqmeasgapoutatt', models.IntegerField(blank=True, null=True)),
                ('interfreqnomeasgapoutatt', models.IntegerField(blank=True, null=True)),
                ('interx2outsucc', models.IntegerField(blank=True, null=True)),
                ('interx2outatt', models.IntegerField(blank=True, null=True)),
                ('interx2insucc', models.IntegerField(blank=True, null=True)),
                ('interx2inatt', models.IntegerField(blank=True, null=True)),
                ('inters1outsucc', models.IntegerField(blank=True, null=True)),
                ('inters1outatt', models.IntegerField(blank=True, null=True)),
                ('inters1insucc', models.IntegerField(blank=True, null=True)),
                ('inters1inatt', models.IntegerField(blank=True, null=True)),
                ('dltransmissionnackedretrans', models.IntegerField(blank=True, null=True)),
                ('dltransmissionretrans0_600', models.IntegerField(blank=True, null=True)),
                ('ultransmissionnackedretrans', models.IntegerField(blank=True, null=True)),
                ('ultransmissionretrans0_600', models.IntegerField(blank=True, null=True)),
                ('connectno', models.IntegerField(blank=True, null=True)),
                ('connectmax', models.IntegerField(blank=True, null=True)),
                ('totalprbdl', models.IntegerField(blank=True, null=True)),
                ('totalprbul', models.IntegerField(blank=True, null=True)),
                ('sitestatus', models.CharField(blank=True, max_length=100, null=True)),
                ('create_at', models.DateTimeField(default=django.utils.timezone.now)),
                ('modify_at', models.DateTimeField(auto_now=True)),
                ('region', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.region')),
                ('sitebasicinfo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo')),
                ('sitephyinfo', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitephyinfo')),
            ],
        ),
    ]
