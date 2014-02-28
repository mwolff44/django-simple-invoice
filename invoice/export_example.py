from .models import Invoice


def gather_data_and_update_flags(test=True):
    invoices = Invoice.objects.filter(is_exported__in=('invoice_only',
                                                       'no'))

    data = []
    for invoice in invoices:
        # Dummy example, you have to impement it yourself ;)
        data.append([invoice.invoice_date, invoice.total(), ])
    return data
