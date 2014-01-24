from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.http import HttpResponse

from invoice.models import Invoice
from invoice.pdf import draw_pdf
from invoice.utils import pdf_response

from os.path import getsize
from django.core.servers.basehttp import FileWrapper


def pdf_dl_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)

    if invoice.is_pdf_generated():
        # Serving file is not Django's job
        # If this need an optimisation, see X-sendfile mod (Apache/nginx)
        wrapper = FileWrapper(file(invoice.pdf_path()))
        response = HttpResponse(wrapper, content_type='text/plain')
        response['Content-Disposition'] = 'attachment; filename="%s"' %\
            invoice.file_name()
        response['Content-Length'] = getsize(invoice.pdf_path())
        return response
    else:
        messages.add_message(request, messages.ERROR,
                             _(u"You have to generate the PDF before!"))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def pdf_gen_view(request, pk):
    invoice = get_object_or_404(Invoice, pk=pk)
    invoice.generate_pdf()
    messages.add_message(request, messages.INFO,
                         _(u"The PDF have been generated."))
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
def pdf_user_view(request, invoice_id):
    invoice = get_object_or_404(Invoice, invoice_id=invoice_id)
    return pdf_response(draw_pdf, invoice.file_name(), invoice)
