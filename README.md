Django Simple Invoice
==============

# Overview

Django-simple-invoice is a fork of [django-invoice (by simonluijk)](https://github.com/simonluijk/django-invoice "django-invoice (by simonluijk)") which works without django-addressbook.

# Requirements

* Python (2.6, 2.7)
* Django (1.5, 1.6)

# Installation

Install using `pip`...

    pip install django-simple-invoice
    pip install django_extensions
    pip install reportlab

# Setup

Add it to your `INSTALLED_APPS` setting.

    INSTALLED_APPS = (
        ...
        'invoice',
    )

Run the following command

	python manage.py syncdb --migrate

You can add some settings to your `settings.py` to customize the invoice.

	INV_MODULE = 'invoice_mod'
	INV_CURRENCY = u'EUR'
	INV_CURRENCY_SYMBOL = u'€'
	INV_LOGO = join(PROJECT_ROOT,'tocollect/img/logo.jpg')

# Configure the billing address

Each invoice is link to a model. For exemple, I for a simple user that buy something on your site, the model will be the UserProfil's model.

Invoice will be found the billing address using some property in your model.

	class UserProfile(models.Model):
    	user = models.ForeignKey(User, null=True, blank=True)
    	contact_name = models.CharField(u'Nom du contact', max_length=255, null=True, blank=True)
    	phone = models.CharField(u'Téléphone', max_length=255)
    	fax = models.CharField(u'Fax', max_length=255, blank=True, null=True)
       	address_1 = models.CharField(u'Adresse', max_length=255)
    	address_2 = models.CharField(u'Supplément adresse 1', max_length=255, blank=True, null=True)
    	address_3 = models.CharField(u'Supplément adresse 2', max_length=255, blank=True, null=True)
    	postal_code = models.CharField(u'Code postal', max_length=100)
    	city = models.CharField(u'Ville', max_length=255)
    	created_date = models.DateField(u'Date de création', auto_now_add=True)

    	@property
    	def invoice_address_one(self):
    	    return self.address_1
    	@property
    	def invoice_address_two(self):
        	return self.address_2
    	@property
    	def invoice_town(self):
    	    return self.city
    	@property
    	def invoice_postcode(self):
    		return self.postal_code
        @property
        def invoice_contact_name(self):
            return self.contact_name
        @property
        def email(self):
            return self.mail

Here, differents property which you can add to your model to set the billing address :
`invoice_address_one`, `invoice_address_two`, `invoice_town`, `invoice_county`, `invoice_postcode`, `invoice_contact_name`


## Customize invoice numbering

Add to your `settings.py` :

    INV_ID_MODULE = 'invoice_mod.numbering'

This module must have a method called `encode` that take the invoice PK and return the invoice number :

    def encode(pk):
        # ...

## Customize invoice file naming

Add to your `settings.py` :

    INV_NAME_MODULE = 'invoice_mod.naming'

This module must have a method called `filename` that take the invoice object and return the invoice file name (with the extension) :

    def filename(invoice):
        # ...


## Customize invoice export

If you want to use the export feature, add to your `settings.py` :

    INV_EXPORT_MODULE = 'invoice_mod.export'

This module must have a method called `gather_data_and_update_flags`. The method's goal is to return a list of rows and update flags (`is_exported`). It takes one argument `test`, if `True` you shouldn't update flag. Here is a dummy example:

    def gather_data_and_update_flags(test):
        invoices = Invoice.objects.filter(is_exported__in=('invoice_only',
                                                           'no'))
        data = []
        for invoice in invoices:
            # Dummy example, you have to implement it yourself ;)
            data.append([invoice.invoice_date, invoice.total(), ])
            if not test:
                invoice.is_exported = 'yes'
        return data

Example of data returned:

    data = [('2014-02-05', '200.00'), ('2014-02-20', '500.00'), ]

It will be your job to manage the `is_exported` fields for `Invoice` and `InvoicePayment`. There is three choices for `Invoice.is_exported`:
- `no` : Ǹothing from that invoice has been exported
- `invoice_only` : The invoice (aka. the items) has been exported, but not the payments
- `yes` : Everything has been exported, invoice and payments
