# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf.urls import patterns, url

from invoice.models import Invoice, InvoiceItem, Currency, InvoicePayment,\
    Export
from invoice.views import pdf_dl_view, pdf_gen_view, export_view,\
    export_test_view
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

    def get_readonly_fields(self, request, obj=None):
        if hasattr(obj, 'is_exported'):
            if obj.is_exported in ('invoice_only', 'yes'):
                return ['credit_note_related_link', 'is_credit_note',
                        'invoice_related_link', 'recipient', 'invoice_date',
                        'draft', 'currency', 'invoice_cost_code']
        return ['credit_note_related_link', 'is_credit_note',
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


class ExportAdmin(admin.ModelAdmin):
    list_display = (
        'pk', 'date',
    )
    readonly_fields = ['date', 'file_link', ]
    exclude = ['file', ]

    def get_urls(self):
        urls = super(ExportAdmin, self).get_urls()
        wrapped_export_view = self.admin_site.admin_view(export_view)
        wrapped_export_test_view = self.admin_site.admin_view(export_test_view)
        urls = patterns(
            '',
            url(r'^do_it/$', wrapped_export_view, name='export_accounts'),
            url(r'^do_it/test$', wrapped_export_test_view,
                name='export_accounts_test'),
        ) + urls
        return urls


admin.site.register(Invoice, InvoiceAdmin)
admin.site.register(Currency)
admin.site.register(Export, ExportAdmin)
