from django.conf import settings


def platform_context(request):
    return {
        "platform_name": "IdentityForge",
        "synthetic_data_only": settings.SYNTHETIC_DATA_ONLY,
        "ai_disclaimer": settings.AI_MODEL_DISCLAIMER,
    }
