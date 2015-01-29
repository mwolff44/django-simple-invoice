# -*- coding: utf-8 -*-
from datetime import date
from decimal import Decimal
from StringIO import StringIO
from email.mime.application import MIMEApplication
from email.MIMEImage import MIMEImage
from os.path import join, isfile

from django.db import models
from django.db.models import Max
from django.conf import settings
from django_extensions.db.models import TimeStampedModel
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from django.template import Context
from django.utils.translation import ugettext_lazy as _
from django.core import urlresolvers
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver
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

    class Meta:
        verbose_name = _(u"currency")
        verbose_name_plural = _(u"currencies")


class InvoiceManager(models.Manager):
    def get_invoiced(self):
        return self.filter(invoiced=True, draft=False)

    def get_due(self):
        return self.filter(invoice_date__lte=date.today(),
                           invoiced=False,
                           draft=False)


class Invoice(TimeStampedModel):
    EXPORTED_CHOICES = (
        ('no', _(u'no')),
        ('invoice_only', _(u'Invoice only')),
        ('yes', _(u'yes')),
    )

    recipient = models.ForeignKey(app_settings.INV_CLIENT_MODULE,
                                  verbose_name=_(u'recipient'))
    currency = models.ForeignKey(Currency, blank=True, null=True,
                                 verbose_name=_(u'currency'))
    number = models.IntegerField(_(u'number'), db_index=True, blank=True, default=0)
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
    # Updated when the invoice is created
    is_credit_note = models.BooleanField(_(u"Is credit note"), default=False,
                                         editable=False)
    invoice_related = models.OneToOneField("self", blank=True, null=True,
                                           related_name="credit_note",
                                           verbose_name=_(u'Invoice related'),
                                           editable=False)
    is_paid = models.BooleanField(_(u"is paid"), editable=False, default=True)
    is_exported = models.CharField(max_length=20, editable=False,
                                   choices=EXPORTED_CHOICES,
                                   default='no')

    def credit_note_related_link(self):
        if ((self.credit_note) and (not self.invoice_related) and
           (not self.is_credit_note)):
            change_url = urlresolvers.reverse('admin:invoice_invoice_change',
                                              args=(self.credit_note.pk,))
            return '<a href="%s">%s</a>' % (change_url,
                                            self.credit_note.invoice_id)
        else:
            return self.invoice_id
    credit_note_related_link.short_description = _(u"Credit note")
    credit_note_related_link.allow_tags = True

    def invoice_related_link(self):
        if self.invoice_related and self.is_credit_note:
            change_url = urlresolvers.reverse('admin:invoice_invoice_change',
                                              args=(self.invoice_related.pk,))
            return '<a href="%s">%s</a>' % (change_url,
                                            self.invoice_related.invoice_id)
        else:
            return self.invoice_id
    invoice_related_link.short_description = _(u"Invoice")
    invoice_related_link.allow_tags = True

    objects = InvoiceManager()

    def __unicode__(self):
        return u'%s (%s)' % (self.invoice_id, self.total_amount())

    class Meta:
        ordering = ('-invoice_date', 'id')
        verbose_name = _(u"invoice")
        verbose_name_plural = _(u"invoices")

    def save(self, *args, **kwargs):

        # During the invoice creation we compute the ID with the pk (that's
        # why we save the model before)
        if not self.invoice_id:
            super(Invoice, self).save(*args, **kwargs)
            inv_id_module = importlib.import_module(app_settings.INV_ID_MODULE)
            self.number = self._get_next_number()
            self.invoice_id = inv_id_module.encode(self.pk, self.number)
            kwargs['force_insert'] = False

        # We check if the invoice is paid
        is_paid = False
        if self.is_credit_note:
            # That a credit note, we consider it as "paid" since nobody need
            # to pay for it
            is_paid = True
            self.invoice_related._update_is_paid()
        else:
            try:
                self.credit_note
                # There is a credit note for this invoice
                is_paid = (self.credit_note.total() >= self.total())
            except:
                # No credit note
                total_paid = 0
                for payment in self.payments.all():
                    total_paid += payment.amount
                is_paid = (total_paid >= self.total())
        self.is_paid = is_paid
        super(Invoice, self).save(*args, **kwargs)

    def _get_next_number(self):
        """
        Returnes next invoice number - reset yearly.

        .. warning::

            This is only used to prepopulate ``number`` field on saving new invoice.
            To get invoice number always use ``number`` field.

        .. note::

            To get invoice full number use ``invoice_id`` field.

        :return: string (generated next number)
        """

        # Recupere les facture de l annee
        relative_invoices = Invoice.objects.filter(invoice_date__year=self.invoice_date.year)
        # on prend le numero le plus eleve du champs number, sinon on met 0
        last_number = relative_invoices.aggregate(Max('number'))['number__max'] or 0

        return last_number + 1

    def total_amount(self):
        return format_currency(self.total(), self.currency)
    total_amount.short_description = _(u"total amount")

    def _update_is_paid(self):
        # Call the save() method in order to compute is the invoice is paid
        self.save()

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

    class Meta:
        verbose_name = _(u"invoice item")
        verbose_name_plural = _(u"invoice items")


class InvoicePayment(models.Model):

    METHOD_CHOICES = (
        ('cheque', _(u'cheque')),
        ('virement', _(u'bank transfer')),
    )

    invoice = models.ForeignKey(Invoice, related_name='payments', unique=False,
                                verbose_name=_(u'invoice'))
    amount = models.DecimalField(_(u"amount"), max_digits=8,
                                 decimal_places=2)
    paid_date = models.DateField(_(u"paid date"), default=date.today())
    method = models.CharField(_(u"payment method"), max_length=20,
                              choices=METHOD_CHOICES,
                              blank=True, null=True)
    additional_info = models.CharField(_(u"additional informations"),
                                       max_length=100, blank=True,
                                       null=True,
                                       help_text=_(u"eg. payment id"))
    is_exported = models.BooleanField(_(u"Is exported"), default=False,
                                      editable=False)
    creation_date = models.DateTimeField(_(u"date of creation"),
                                         auto_now_add=True)
    modification_date = models.DateTimeField(_(u"date of modification"),
                                             auto_now=True)

    def __unicode__(self):
        return self.amount

    class Meta:
        verbose_name = _(u"invoice payment")
        verbose_name_plural = _(u"invoice payments")


@receiver(post_save, sender=InvoicePayment)
def payment_saved(sender, instance, using, **kwargs):
    payment = instance
    payment.invoice._update_is_paid()


@receiver(post_delete, sender=InvoicePayment)
def payment_deleted(sender, instance, using, **kwargs):
    payment = instance
    payment.invoice._update_is_paid()


@receiver(post_save, sender=InvoiceItem)
def item_saved(sender, instance, using, **kwargs):
    item = instance
    item.invoice._update_is_paid()


@receiver(post_delete, sender=InvoiceItem)
def item_deleted(sender, instance, using, **kwargs):
    item = instance
    item.invoice._update_is_paid()


class Export(models.Model):
    date = models.DateField(_(u"date"))
    file = models.FileField(_(u"file"), upload_to='invoices/export')

    creation_date = models.DateTimeField(_(u"date of creation"),
                                         auto_now_add=True)
    modification_date = models.DateTimeField(_(u"date of modification"),
                                             auto_now=True)

    def file_link(self):
        if self.file:
            file_url = "%s%s" % (settings.MEDIA_URL, self.file)

            return '<a href="%s">%s</a>' % (file_url,
                                            self.file)
        else:
            return self.file
    file_link.short_description = _(u"file")
    file_link.allow_tags = True
