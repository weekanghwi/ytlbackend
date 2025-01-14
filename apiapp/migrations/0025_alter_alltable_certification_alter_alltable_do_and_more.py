# Generated by Django 4.2.4 on 2023-09-06 08:24

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('apiapp', '0024_sitephyinfo_uid'),
    ]

    operations = [
        migrations.AlterField(
            model_name='alltable',
            name='certification',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.certification'),
        ),
        migrations.AlterField(
            model_name='alltable',
            name='do',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.do'),
        ),
        migrations.AlterField(
            model_name='alltable',
            name='install',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.install'),
        ),
        migrations.AlterField(
            model_name='alltable',
            name='optimization',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.optimization'),
        ),
        migrations.AlterField(
            model_name='alltable',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='alltable',
            name='ssv',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.ssv'),
        ),
        migrations.AlterField(
            model_name='certification',
            name='facapprovestatus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.facapprovestatus'),
        ),
        migrations.AlterField(
            model_name='certification',
            name='pacapprovestatus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.pacapprovestatus'),
        ),
        migrations.AlterField(
            model_name='certification',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='cluster',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.region'),
        ),
        migrations.AlterField(
            model_name='do',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='install',
            name='coicapprovestatus',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.coicapprovestatus'),
        ),
        migrations.AlterField(
            model_name='install',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='material',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='optimization',
            name='optsubcon',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.subcon'),
        ),
        migrations.AlterField(
            model_name='optimization',
            name='opttype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.opttype'),
        ),
        migrations.AlterField(
            model_name='optimization',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='optissue',
            name='issuetype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.optissuetype'),
        ),
        migrations.AlterField(
            model_name='optissue',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='sitebasicinfo',
            name='cluster',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.cluster'),
        ),
        migrations.AlterField(
            model_name='sitebasicinfo',
            name='contracttype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.contracttype'),
        ),
        migrations.AlterField(
            model_name='sitebasicinfo',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.region'),
        ),
        migrations.AlterField(
            model_name='sitebasicinfo',
            name='siteconfig',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.siteconfig'),
        ),
        migrations.AlterField(
            model_name='sitebasicinfo',
            name='state',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.state'),
        ),
        migrations.AlterField(
            model_name='sitephyinfo',
            name='antennatype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.antennatype'),
        ),
        migrations.AlterField(
            model_name='sitephyinfo',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='ssv',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='ssv',
            name='ssvsubcon',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.subcon'),
        ),
        migrations.AlterField(
            model_name='ssvissue',
            name='issuetype',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.ssvissuetype'),
        ),
        migrations.AlterField(
            model_name='ssvissue',
            name='sitebasicinfo',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.sitebasicinfo'),
        ),
        migrations.AlterField(
            model_name='state',
            name='region',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='apiapp.region'),
        ),
    ]
