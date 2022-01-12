from datetime import datetime, timezone
from os import environ
import humanize


time_locale = environ.get(
    'LC_TIME', environ.get('LC_ALL', 'en_US')
).split('.')[0]
try:
    humanize.i18n.activate(time_locale)
except Exception:
    print(f'Time localization unavailable for locale `{time_locale}`')
THREE_DAYS = 60*60*24*3


def humanize_datetime(dt):
    delta = datetime.now(timezone.utc) - dt
    if delta.total_seconds() <= THREE_DAYS:
        return humanize.naturaltime(delta)
    else:
        return humanize.naturaldate(dt)
