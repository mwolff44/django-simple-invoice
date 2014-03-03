# -*- coding: utf-8 -*-
from django.conf import settings
from django.utils.text import get_valid_filename
from django.core.files.storage import FileSystemStorage
from django.utils.translation import ugettext_lazy as _
try:
    from django.utils import importlib
except ImportError:
    import importlib

import csv
from datetime import datetime, date
from os.path import join, split

from .models import Export
from .conf import settings as inv_settings

import logging
logger = logging.getLogger(__name__)


def export(test=True):
    data = gather_data_and_update_flags(test)
    if data == []:
        raise Exception(u"%s" % _(u"No data to export!"))
    elif not data:
        logger.error(u"%s" % _(u"Error when fetching data - Data empty."))
        raise Exception(u"%s" % _(u"Error when fetching data"
                                  u" Export cancelled!"))

    # File name
    if test:
        filename = get_valid_filename("test_%s.csv" % date.today())
    else:
        filename = get_valid_filename("%s.csv" % date.today())
    mediafilepath = join("invoices/export/", filename)
    filepath = join(settings.MEDIA_ROOT, mediafilepath)

    # Ensure that we got an available file name
    fss = FileSystemStorage()
    filepath = fss.get_available_name(filepath)

    # If the file name change, we update the media file path
    filename = split(filepath)[1]
    mediafilepath = join("invoices/export/", filename)

    # Write the file on the FS, and create the Export object if we are not in
    # test mode
    with open(filepath, "w") as csvfile:
        exportwriter = csv.writer(csvfile, delimiter=';',
                                  quoting=csv.QUOTE_ALL)

        # We do this because CSV doesn't support directly Unicode and UTF-8
        # http://docs.python.org/2/library/csv.html#examples
        for row in data:
            r = []
            for field in row:
                r.append(("%s" % field).strip().encode("utf-8"))
            exportwriter.writerow(r)

        if not test:
            export = Export(date=datetime.today(),
                            file=mediafilepath)
            export.save()

    return settings.MEDIA_URL + mediafilepath


def utf_8_encoder(unicode_csv_data):
    for line in unicode_csv_data:
        yield line.encode('utf-8')


def gather_data_and_update_flags(*args, **kwargs):
    try:
        data_module = importlib.import_module(inv_settings.INV_EXPORT_MODULE)
    except:
        logger.error(u"%s" % _(u"Export module not found! %s " %
                               inv_settings.INV_EXPORT_MODULE))
        raise Exception(u"%s" % _(u"Export module not found!"))

    return data_module.gather_data_and_update_flags(*args, **kwargs)
