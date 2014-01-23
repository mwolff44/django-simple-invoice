try:
    from django.utils import importlib
except ImportError:
    import importlib

from invoice.conf import settings


def header_func(*args, **kwargs):
    inv_module = importlib.import_module(settings.INV_MODULE)
    inv_module.draw_header(*args, **kwargs)


def address_func(*args, **kwargs):
    inv_module = importlib.import_module(settings.INV_MODULE)
    inv_module.draw_address(*args, **kwargs)


def footer_func(*args, **kwargs):
    inv_module = importlib.import_module(settings.INV_MODULE)
    inv_module.draw_footer(*args, **kwargs)


def draw_pdf(*args, **kwargs):
    inv_module = importlib.import_module(settings.INV_MODULE)
    inv_module.draw_pdf(*args, **kwargs)
