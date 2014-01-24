# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from StringIO import StringIO
from email.mime.application import MIMEApplication
from os.path import join, isfile

from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel
from django.template.loader import render_to_string
from django.core.mail import EmailMessage
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils import importlib
except ImportError:
    import importlib

from .utils import format_currency
from .conf import settings as app_settings
from .pdf import draw_pdf


class Currency(models.Model):
    code = models.CharField(unique=True, max_length=3)
    pre_symbol = models.CharField(blank=True, max_length=1)
    post_symbol = models.CharField(blank=True, max_length=1)

    def __unicode__(self):
        return self.code


class InvoiceManager(models.Manager):
    def get_invoiced(self):
        return self.filter(invoiced=True, draft=False)

    def get_due(self):
        return self.filter(invoice_date__lte=date.today(),
                           invoiced=False,
                           draft=False)


class Invoice(TimeStampedModel):

    METHOD_CHOICES = (
        ('cheque', _(u'Chèque')),
        ('virement', _(u'Virement')),
    )

    recipient = models.ForeignKey(app_settings.INV_CLIENT_MODULE,
                                  verbose_name=_(u'recipient'))
    currency = models.ForeignKey(Currency, blank=True, null=True,
                                 verbose_name=_(u'currency'))
    invoice_id = models.CharField(_(u'invoice ID'), unique=True, max_length=10,
                                  null=True, blank=True, editable=False)
    invoice_date = models.DateField(_(u'invoice date'), default=date.today)
    # cost accounting code
    invoice_cost_code = models.CharField(_(u"cost accounting code"),
                                         max_length=10, blank=True, null=True)
    invoiced = models.BooleanField(_(u"invoiced"), default=False)
    draft = models.BooleanField(_(u"draft"), default=False)

    paid_date = models.DateField(_(u"paid date"), blank=True, null=True)
    payment_method = models.CharField(_(u"payment method"), max_length=20,
                                      choices=METHOD_CHOICES,
                                      blank=True, null=True)
    payment_additional_info = models.CharField(_(u"additional informations"),
                                               max_length=20, blank=True,
                                               null=True,
                                               help_text=_(u"eg. payment id"))
    creation_date = models.DateTimeField(_(u"date of creation"),
                                         auto_now_add=True)
    modification_date = models.DateTimeField(_(u"date of modification"),
                                             auto_now=True)

    objects = InvoiceManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.invoice_id, self.total_amount())

    class Meta:
        ordering = ('-invoice_date', 'id')

    def save(self, *args, **kwargs):
        super(Invoice, self).save(*args, **kwargs)

        if not self.invoice_id:
            inv_id_module = importlib.import_module(app_settings.INV_ID_MODULE)
            self.invoice_id = inv_id_module.encode(self.pk)
            kwargs['force_insert'] = False
            super(Invoice, self).save(*args, **kwargs)

    def total_amount(self):
        return format_currency(self.total(), self.currency)
    total_amount.short_description = _(u"total amount")

    def total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total = total + item.total()
        return total
    total.short_description = _(u"total")

    def file_name(self):
        return u'invoice_%s.pdf' % self.invoice_id

    def generate_pdf(self):
        draw_pdf(self.pdf_path(), self)

    def is_pdf_generated(self):
        if isfile(self.pdf_path()):
            return True
        else:
            return False

    def pdf_path(self):
        # Beware, the file might not be here if it has not been generated yet
        return join(app_settings.INV_PDF_DIR, self.file_name())

    def send_invoice(self):
        pdf = StringIO()
        draw_pdf(pdf, self)
        pdf.seek(0)

        attachment = MIMEApplication(pdf.read())
        attachment.add_header("Content-Disposition", "attachment",
                              filename=self.file_name())
        pdf.close()

        subject = app_settings.INV_EMAIL_SUBJECT %\
            {"invoice_id": self.invoice_id}
        email = EmailMessage(subject=subject, to=[self.recipient.email])
        email.body = render_to_string("invoice/invoice_email.txt", {
            "invoice": self,
            "SITE_NAME": settings.SITE_NAME,
            "INV_CURRENCY": app_settings.INV_CURRENCY,
            "INV_CURRENCY_SYMBOL": app_settings.INV_CURRENCY_SYMBOL,
            "SUPPORT_EMAIL": settings.MANAGERS[0][1],
        })
        email.attach(attachment)
        email.send()

        self.invoiced = True
        self.save()


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, related_name='items', unique=False,
                                verbose_name=_(u'invoice'))
    description = models.CharField(_(u"description"), max_length=100)
    unit_price = models.DecimalField(_(u"unit price"), max_digits=8,
                                     decimal_places=2)
    quantity = models.DecimalField(_(u"quantity"), max_digits=8,
                                   decimal_places=2, default=1)
    creation_date = models.DateTimeField(_(u"date of creation"),
                                         auto_now_add=True)
    modification_date = models.DateTimeField(_(u"date of modification"),
                                             auto_now=True)

    def total(self):
        total = Decimal(str(self.unit_price * self.quantity))
        return total.quantize(Decimal('0.01'))

    def __unicode__(self):
        return self.description
