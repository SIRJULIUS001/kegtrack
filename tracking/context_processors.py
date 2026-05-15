# tracking/context_processors.py

from tracking.models import KegSystemConfig

def keg_config(request):
    config, _ = KegSystemConfig.objects.get_or_create(id=1)
    return {"config": config}