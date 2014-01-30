# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from StringIO import StringIO
from email.mime.application import MIMEApplication
from email.MIMEImage import MIMEImage
from os.path import join, isfile

from django.db import models
from django.conf import settings
from django_extensions.db.models import TimeStampedModel
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
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

    def is_paid(self):
        total_paid = 0
        for payment in self.payments.all():
            total_paid += payment.amount
        return (total_paid >= self.total())
    is_paid.short_description = _(u"is paid?")
    is_paid.boolean = True

    def last_payment(self):
        payments = self.payments.order_by('-paid_date')
        if payments:
            return payments[0]
        else:
            return None
    last_payment.short_description = _(u"last payment")

    def total(self):
        total = Decimal('0.00')
        for item in self.items.all():
            total = total + item.total()
        return total
    total.short_description = _(u"total")

    def file_name(self):
        inv_name_module = importlib.import_module(app_settings.INV_NAME_MODULE)
        return inv_name_module.filename(self)

    def generate_pdf(self):
        return draw_pdf(self.pdf_path(), self)

    def is_pdf_generated(self):
        return isfile(self.pdf_path())

    def pdf_path(self):
        # Beware, the file might not be here if it has not been generated yet
        return join(app_settings.INV_PDF_DIR, self.file_name())

    def send_invoice(self, to_email=None, subject=None,
                     template='invoice_email', images=()):
        if self.recipient.email or to_email:
            pdf = StringIO()
            draw_pdf(pdf, self)
            pdf.seek(0)

            attachment = MIMEApplication(pdf.read())
            attachment.add_header("Content-Disposition", "attachment",
                                  filename=self.file_name())
            pdf.close()

            if not to_email:
                to_email = self.recipient.email
            if not subject:
                subject = app_settings.INV_EMAIL_SUBJECT %\
                    {"invoice_id": self.invoice_id}

            text_tmpl = get_template('invoice/email/%s.txt' % template)
            html_tmpl = get_template('invoice/email/%s.html' % template)

            email_context = Context({
                'invoice': self,
                'date': date.today(),
                "SITE_NAME": settings.SITE_NAME,
                "INV_CURRENCY": app_settings.INV_CURRENCY,
                "INV_CURRENCY_SYMBOL": app_settings.INV_CURRENCY_SYMBOL, })

            text_content = text_tmpl.render(email_context)
            html_content = html_tmpl.render(email_context)

            email = EmailMultiAlternatives(subject=subject, body=text_content,
                                           to=[to_email])
            email.attach_alternative(html_content, "text/html")
            email.attach(attachment)

            for img in images:
                fp = open(join(settings.STATIC_ROOT, img[0]), 'rb')
                msgImage = MIMEImage(fp.read())
                fp.close()
                msgImage.add_header('Content-ID', '<' + img[1] + '>')
                email.attach(msgImage)

            email.send()

            self.invoiced = True
            self.save()

            return True
        else:
            return False


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


class InvoicePayment(models.Model):

    METHOD_CHOICES = (
        ('cheque', _(u'Chèque')),
        ('virement', _(u'Virement')),
    )

    invoice = models.ForeignKey(Invoice, related_name='payments', unique=False,
                                verbose_name=_(u'invoice'))
    amount = models.DecimalField(_(u"amount"), max_digits=8,
                                 decimal_places=2)
    paid_date = models.DateField(_(u"paid date"), blank=True, null=True)
    method = models.CharField(_(u"payment method"), max_length=20,
                              choices=METHOD_CHOICES,
                              blank=True, null=True)
    additional_info = models.CharField(_(u"additional informations"),
                                       max_length=20, blank=True,
                                       null=True,
                                       help_text=_(u"eg. payment id"))
    creation_date = models.DateTimeField(_(u"date of creation"),
                                         auto_now_add=True)
    modification_date = models.DateTimeField(_(u"date of modification"),
                                             auto_now=True)
