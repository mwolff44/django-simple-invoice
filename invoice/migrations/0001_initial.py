# -*- coding: utf-8 -*-
from south.utils import datetime_utils as datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

from django.conf import settings as app_settings
#company_orm_label = '%s.%s' % (app_settings.INV_CLIENT_MODULE._meta.app_label, app_settings.INV_CLIENT_MODULE._meta.object_name)
#company_model_label = '%s.%s' % (app_settings.INV_CLIENT_MODULE._meta.app_label, app_settings.INV_CLIENT_MODULE._meta.module_name)
app_model_label = '%s' % app_settings.INV_CLIENT_MODULE

class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Currency'
        db.create_table(u'invoice_currency', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=3)),
            ('pre_symbol', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
            ('post_symbol', self.gf('django.db.models.fields.CharField')(max_length=1, blank=True)),
        ))
        db.send_create_signal(u'invoice', ['Currency'])

        # Adding model 'Invoice'
        db.create_table(u'invoice_invoice', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, blank=True)),
            ('recipient', self.gf('django.db.models.fields.related.ForeignKey')(to=orm[app_settings.INV_CLIENT_MODULE])),
            ('number', self.gf('django.db.models.fields.IntegerField')(default=0, db_index=True, blank=True)),
            ('currency', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['invoice.Currency'], null=True, blank=True)),
            ('invoice_id', self.gf('django.db.models.fields.CharField')(max_length=10, unique=True, null=True, blank=True)),
            ('invoice_date', self.gf('django.db.models.fields.DateField')(default=datetime.date.today)),
            ('invoice_cost_code', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('invoiced', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('draft', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_credit_note', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('is_paid', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('is_exported', self.gf('django.db.models.fields.CharField')(default='no', max_length=20)),
            ('invoice_related', self.gf('django.db.models.fields.related.OneToOneField')(blank=True, related_name='credit_note', unique=True, null=True, to=orm['invoice.Invoice'])),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'invoice', ['Invoice'])

        # Adding model 'InvoiceItem'
        db.create_table(u'invoice_invoiceitem', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('invoice', self.gf('django.db.models.fields.related.ForeignKey')(related_name='items', to=orm['invoice.Invoice'])),
            ('description', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('unit_price', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('quantity', self.gf('django.db.models.fields.DecimalField')(default=1, max_digits=8, decimal_places=2)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'invoice', ['InvoiceItem'])

        # Adding model 'InvoicePayment'
        db.create_table(u'invoice_invoicepayment', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('invoice', self.gf('django.db.models.fields.related.ForeignKey')(related_name='payments', to=orm['invoice.Invoice'])),
            ('amount', self.gf('django.db.models.fields.DecimalField')(max_digits=8, decimal_places=2)),
            ('paid_date', self.gf('django.db.models.fields.DateField')()),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('additional_info', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('is_exported', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'invoice', ['InvoicePayment'])

        # Adding model 'Export'
        db.create_table(u'invoice_export', (
            (u'id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('creation_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('modification_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal(u'invoice', ['Export'])


    def backwards(self, orm):
        # Deleting model 'Currency'
        db.delete_table(u'invoice_currency')

        # Deleting model 'Invoice'
        db.delete_table(u'invoice_invoice')

        # Deleting model 'InvoiceItem'
        db.delete_table(u'invoice_invoiceitem')

        # Deleting model 'InvoicePayment'
        db.delete_table(u'invoice_invoicepayment')

        # Deleting model 'Export'
        db.delete_table(u'invoice_export')


    models = {
        app_model_label: app_settings.INV_MODEL_LABEL,
        u'invoice.currency': {
            'Meta': {'object_name': 'Currency'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '3'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'post_symbol': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'}),
            'pre_symbol': ('django.db.models.fields.CharField', [], {'max_length': '1', 'blank': 'True'})
        },
        u'invoice.export': {
            'Meta': {'object_name': 'Export'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'})
        },
        u'invoice.invoice': {
            'Meta': {'ordering': "('-invoice_date', 'id')", 'object_name': 'Invoice'},
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'currency': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['invoice.Currency']", 'null': 'True', 'blank': 'True'}),
            'draft': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice_cost_code': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'invoice_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.date.today'}),
            'invoice_id': ('django.db.models.fields.CharField', [], {'max_length': '10', 'unique': 'True', 'null': 'True', 'blank': 'True'}),
            'invoice_related': ('django.db.models.fields.related.OneToOneField', [], {'blank': 'True', 'related_name': "'credit_note'", 'unique': 'True', 'null': 'True', 'to': u"orm['invoice.Invoice']"}),
            'invoiced': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_credit_note': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_exported': ('django.db.models.fields.CharField', [], {'default': "'no'", 'max_length': '20'}),
            'is_paid': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'blank': 'True'}),
            'number': ('django.db.models.fields.IntegerField', [], {'db_index': 'True', 'blank': 'True'}),
            'recipient': ('django.db.models.fields.related.ForeignKey', [], {'to': u"orm['%s']" % app_settings.INV_CLIENT_MODULE})
        },
        u'invoice.invoiceitem': {
            'Meta': {'object_name': 'InvoiceItem'},
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'description': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'items'", 'to': u"orm['invoice.Invoice']"}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'quantity': ('django.db.models.fields.DecimalField', [], {'default': '1', 'max_digits': '8', 'decimal_places': '2'}),
            'unit_price': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'})
        },
        u'invoice.invoicepayment': {
            'Meta': {'object_name': 'InvoicePayment'},
            'additional_info': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'amount': ('django.db.models.fields.DecimalField', [], {'max_digits': '8', 'decimal_places': '2'}),
            'creation_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            u'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'invoice': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'payments'", 'to': u"orm['invoice.Invoice']"}),
            'is_exported': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'modification_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'paid_date': ('django.db.models.fields.DateField', [], {'default': 'datetime.datetime(2014, 2, 27, 0, 0)'})
        }
    }

    complete_apps = ['invoice']