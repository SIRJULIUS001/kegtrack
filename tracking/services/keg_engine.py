from tracking.models import KegSession


def consume_keg(business, keg_type, volume):

    session = KegSession.objects.filter(
        keg__keg_type=keg_type,
        keg__business=business,   # ✅ multi-tenant safe
        status="open"
    ).first()

    if not session:
        return None

    session.consumed_volume += volume
    session.save()

    return session