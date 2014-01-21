from django import forms
from django.contrib.auth.models import User
from invoice.models import Invoice


class InvoiceAdminForm(forms.ModelForm):
    class Meta:
        model = Invoice
