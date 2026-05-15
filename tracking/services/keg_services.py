from tracking.models import KegSession


def open_keg(keg, user):

    # prevent multiple open sessions
    existing = KegSession.objects.filter(keg=keg, status="open").first()
    if existing:
        return existing

    session = KegSession.objects.create(
        keg=keg,
        opened_by=user,
        expected_remaining_litres=keg.keg_type.capacity_litres
    )

    return session

def record_sale(session, litres_sold):

    session.expected_remaining_litres -= litres_sold

    if session.expected_remaining_litres < 0:
        session.expected_remaining_litres = 0

    session.save()

    return session

from django.utils import timezone


def close_keg(session):

    session.status = "closed"
    session.closed_at = timezone.now()
    session.save()

    return session

def calculate_litres(measured_weight, empty_weight, density=1.01):

    return max((measured_weight - empty_weight) / density, 0)

from tracking.models import KegVerification
from tracking.models import KegSystemConfig


def verify_keg(session, user, measured_weight, photo, trigger):

    config = KegSystemConfig.objects.first()

    keg = session.keg
    empty_weight = keg.keg_type.empty_weight

    # calculate actual litres
    actual_litres = calculate_litres(
        measured_weight,
        empty_weight,
        config.beer_density
    )

    expected = session.expected_remaining_litres

    variance = expected - actual_litres

    verification = KegVerification.objects.create(
        keg=keg,
        session=session,
        trigger=trigger,
        measured_weight=measured_weight,
        calculated_litres=actual_litres,
        variance=variance,
        photo=photo,
        verified_by=user
    )

    # update fraud system
    update_fraud_signal(keg.business, variance)

    return verification
from tracking.models import KegFraudSignal


def update_fraud_signal(business, variance):

    signal, _ = KegFraudSignal.objects.get_or_create(business=business)

    signal.total_variance += abs(variance)

    # simple scoring logic (can upgrade later)
    signal.fraud_score = min(signal.total_variance * 2, 100)

    if signal.fraud_score > 70:
        signal.flagged = True

    signal.save()

    return signal

from tracking.models import BusinessKegPolicy


def check_policy(business, variance):

    policy = BusinessKegPolicy.objects.filter(business=business).first()

    if not policy:
        return False

    if abs(variance) > policy.max_variance_percent:
        return True  # violation

    return False