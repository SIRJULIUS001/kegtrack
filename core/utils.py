# core/utils.py

from core.models import AuditLog


def log_action(user, action, instance, changes=None):
    """
    Central audit logger
    """

    AuditLog.objects.create(
        business=getattr(user, "business", None),
        user=user,
        action=action,
        model_name=instance.__class__.__name__,
        object_id=str(instance.id),
        changes=changes or {}
    )


def get_setting(key, business=None):
    """
    Fetch system setting (business → fallback to global)
    """

    from core.models import SystemSetting

    setting = SystemSetting.objects.filter(
        key=key,
        business=business
    ).first()

    if not setting:
        setting = SystemSetting.objects.filter(
            key=key,
            business__isnull=True
        ).first()

    return setting.value if setting else None