# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf.urls import patterns
from django.utils.translation import ugettext_lazy as _
from invoice.models import Invoice, InvoiceItem, Currency
from invoice.views import pdf_dl_view, pdf_gen_view
from invoice.forms import InvoiceAdminForm


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem


class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline, ]
    fieldsets = [
        (None, {
            'fields': ['recipient', 'invoice_date', 'draft',
                       'currency', 'invoice_cost_code']
        }),
        (_(u'Payment'), {
            'fields': ['paid_date', 'payment_method',
                       'payment_additional_info']
        }),
    ]

    search_fields = ('invoice_id',)
    list_display = (
        'invoice_id',
        'total_amount',
        'recipient',
        'draft',
        'invoice_date',
        'invoiced',
        'paid_date',
    )
    form = InvoiceAdminForm
    actions = ['send_invoice', ]

    def get_urls(self):
        urls = super(InvoiceAdmin, self).get_urls()
        wrapped_pdf_dl_view = self.admin_site.admin_view(pdf_dl_view)
        wrapped_pdf_gen_view = self.admin_site.admin_view(pdf_gen_view)
        urls = patterns(
            '',
            (r'^(.+)/pdf/download/$', wrapped_pdf_dl_view),
            (r'^(.+)/pdf/generate/$', wrapped_pdf_gen_view),
        ) + urls
        return urls

    def send_invoice(self, request, queryset):
        for invoice in queryset.all():
            invoice.send_invoice()

    send_invoice.short_description = _(u"Send invoice to client")


admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Currency)
