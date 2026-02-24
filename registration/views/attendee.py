from datetime import date

from registration.models import Attendee, BanList


def get_attendee_age(attendee: Attendee):
    born = attendee.birthdate
    today = date.today()
    age = today.year - born.year - ((today.month, today.day) < (born.month, born.day))
    return age


def check_ban_list(firstName, lastName, email):
    return BanList.objects.filter(
        firstName__iexact=firstName, lastName__iexact=lastName, email__iexact=email
    ).exists()
