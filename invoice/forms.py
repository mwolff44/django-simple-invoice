from django import forms

from invoice.models import Invoice


class InvoiceAdminForm(forms.ModelForm):
    class Meta:
        model = Invoice
