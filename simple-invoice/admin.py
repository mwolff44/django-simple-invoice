# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf.urls import patterns

from invoice.models import Invoice, InvoiceItem, Currency, InvoicePayment
from invoice.views import pdf_dl_view, pdf_gen_view
from invoice.forms import InvoiceAdminForm
from invoice.admin_actions import send_invoice, generate_credit_note


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem


class InvoicePaymentInline(admin.TabularInline):
    model = InvoicePayment


class InvoiceAdmin(admin.ModelAdmin):
    inlines = [InvoiceItemInline, InvoicePaymentInline, ]
    fieldsets = [
        (None, {
            'fields': ['recipient', 'invoice_date', 'draft',
                       'currency', 'invoice_cost_code']
        }),
        ('Credit Note', {
            'classes': ('collapse', ),
            'fields': ['is_credit_note', 'credit_note_related_link',
                       'invoice_related_link']
        })
    ]
    readonly_fields = ['credit_note_related_link', 'is_credit_note',
                       'invoice_related_link', ]
    search_fields = ('invoice_id',)
    list_filter = ['invoice_date', 'invoiced', 'is_credit_note', 'is_paid', ]
    list_display = (
        'invoice_id',
        'total_amount',
        'recipient',
        'draft',
        'invoice_date',
        'invoiced',
    )
    form = InvoiceAdminForm
    actions = [send_invoice, generate_credit_note, ]

    def has_delete_permission(self, request, obj=None):
        return False

    def get_actions(self, request):
        actions = super(InvoiceAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

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

admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Currency)
