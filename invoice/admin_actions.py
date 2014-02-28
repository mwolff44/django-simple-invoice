# -*- coding: utf-8 -*-
from django.utils.translation import ugettext_lazy as _
from django.shortcuts import redirect
from django.core import urlresolvers
from django.contrib import messages

from invoice.models import Invoice, InvoiceItem


def send_invoice(self, request, queryset):
    for invoice in queryset.all():
        invoice.send_invoice()
send_invoice.short_description = _(u"Send invoice to client")


def generate_credit_note(self, request, queryset):
    last_credite_note_created = None
    for invoice in queryset.all():
        if invoice.is_credit_note:
            messages.add_message(request, messages.ERROR,
                                 _(u"You cannot create a credit note for "
                                   u"a credit note! (%s)" %
                                   invoice.invoice_id))
            continue
        try:
            invoice.credit_note
            messages.add_message(request, messages.ERROR,
                                 _(u"This invoice has already a credit "
                                   u"note a credit note! (%s)" %
                                   invoice.invoice_id))
            continue
        except:
            pass
        credit_note = Invoice(recipient=invoice.recipient,
                              is_credit_note=True,
                              invoice_related=invoice,
                              invoice_cost_code=invoice.invoice_cost_code)
        credit_note.save()
        last_credite_note_created = credit_note
        for invoice_item in invoice.items.all():
            item = InvoiceItem(invoice=credit_note,
                               description=invoice_item.description,
                               unit_price=invoice_item.unit_price,
                               quantity=invoice_item.quantity)
            item.save()
    if last_credite_note_created:
        change_url = urlresolvers.reverse(
            'admin:invoice_invoice_change',
            args=(last_credite_note_created.pk,))
        return redirect(change_url)
generate_credit_note.short_description = _(u"Generate credit note")
