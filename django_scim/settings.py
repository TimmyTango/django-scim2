"""
This module is largely inspired by django-rest-framework settings.

Settings for the SCIM Service Provider are all namespaced in the
SCIM_SERVICE_PROVIDER setting. For example your project's `settings.py`
file might look like this:

SCIM_SERVICE_PROVIDER = {
    'USER_ADAPTER': 'django_scim.adapters.SCIMUser',
    'GROUP_ADAPTER': 'django_scim.adapters.SCIMGroup',
}

This module provides the `scim_settings` object, that is used to access
SCIM Service Provider settings, checking for user settings first, then falling
back to the defaults.
"""
from __future__ import unicode_literals

import importlib
import six

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


# Settings defined by user in root settings file for their project.
USER_SETTINGS = getattr(settings, 'SCIM_SERVICE_PROVIDER', None)

DEFAULTS = {
    'USER_ADAPTER': 'django_scim.adapters.SCIMUser',
    'GROUP_MODEL': 'django.contrib.auth.models.Group',
    'GROUP_ADAPTER': 'django_scim.adapters.SCIMGroup',
    'SERVICE_PROVIDER_CONFIG_MODEL': 'django_scim.models.SCIMServiceProviderConfig',
    'BASE_LOCATION_GETTER': 'django_scim.utils.default_base_scim_location_getter',
    'DOCUMENTATION_URI': None,
    'SCHEME': 'https',
    'NETLOC': None,
    'AUTHENTICATION_SCHEMES': [],
    'WWW_AUTHENTICATE_HEADER': 'Basic realm="django-scim2"',
}

# List of settings that cannot be empty
MANDATORY = (
    'NETLOC',
    'AUTHENTICATION_SCHEMES',
)

# List of settings that may be in string import notation.
IMPORT_STRINGS = (
    'USER_ADAPTER',
    'GROUP_MODEL',
    'GROUP_ADAPTER',
    'SERVICE_PROVIDER_CONFIG_MODEL',
    'BASE_LOCATION_GETTER',
)


def perform_import(val, setting_name):
    """
    If the given setting is a string import notation,
    then perform the necessary import or imports.
    """
    if isinstance(val, six.string_types):
        return import_from_string(val, setting_name)
    elif isinstance(val, (list, tuple)):
        return [import_from_string(item, setting_name) for item in val]
    return val


def import_from_string(val, setting_name):
    """
    Attempt to import a class from a string representation.
    """
    try:
        parts = val.split('.')
        module_path, class_name = '.'.join(parts[:-1]), parts[-1]
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except ImportError as e:
        msg = "Could not import '%s' for setting '%s'. %s: %s." % (val, setting_name, e.__class__.__name__, e)
        raise ImportError(msg)


class SCIMServiceProviderSettings(object):
    """
    A settings object, that allows SCIM Service Provider settings to be accessed as properties.

    Any setting with string import paths will be automatically resolved
    and return the class, rather than the string literal.
    """

    def __init__(self, user_settings=None, defaults=None, import_strings=None, mandatory=None):
        self.user_settings = user_settings or {}
        self.defaults = defaults or {}
        self.import_strings = import_strings or ()
        self.mandatory = mandatory or ()

    def __getattr__(self, attr):
        if attr not in self.defaults.keys():
            raise AttributeError("Invalid SCIMServiceProvider setting: '%s'" % attr)

        try:
            # Check if present in user settings
            val = self.user_settings[attr]
        except KeyError:
            # Fall back to defaults
            val = self.defaults[attr]

        # Coerce import strings into classes
        if val and attr in self.import_strings:
            val = perform_import(val, attr)

        self.validate_setting(attr, val)

        # Cache the result
        setattr(self, attr, val)
        return val

    def validate_setting(self, attr, val):
        if not val and attr in self.mandatory:
            raise AttributeError("SCIMServiceProvider setting: '%s' is mandatory" % attr)


scim_settings = SCIMServiceProviderSettings(USER_SETTINGS, DEFAULTS, IMPORT_STRINGS, MANDATORY)
