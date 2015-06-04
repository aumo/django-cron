from django.utils.translation import ugettext as _
from django.template.defaultfilters import pluralize


def humanize_duration(duration):
    """
    Returns a humanized string representing time difference

    For example: 2 days 1 hour 25 minutes 10 seconds
    """
    days = duration.days
    hours = int(duration.seconds / 3600)
    minutes = int(duration.seconds % 3600 / 60)
    seconds = int(duration.seconds % 3600 % 60)

    parts = []
    if days > 0:
        parts.append(u'%s %s' % (days, pluralize(days, _('day,days'))))

    if hours > 0:
        parts.append(u'%s %s' % (hours, pluralize(hours, _('hour,hours'))))

    if minutes > 0:
        parts.append(u'%s %s' % (minutes, pluralize(minutes, _('minute,minutes'))))

    if seconds > 0:
        parts.append(u'%s %s' % (seconds, pluralize(seconds, _('second,seconds'))))

    return ', '.join(parts) if len(parts) != 0 else _('< 1 second')


class cached_property(object):
    """
    A property that is only computed once per instance and then replaces
    itself with an ordinary attribute. Deleting the attribute resets the
    property.

    Source: https://github.com/bottlepy/bottle/commit/fa7733e075da0d790d809aa3d2f53071897e6f76
    """

    def __init__(self, func):
        self.__doc__ = getattr(func, '__doc__')
        self.func = func

    def __get__(self, obj, cls):
        if obj is None:
            return self
        value = obj.__dict__[self.func.__name__] = self.func(obj)
        return value
