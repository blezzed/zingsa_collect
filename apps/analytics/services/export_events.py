import logging

from apps.analytics.models import DataExportEvent

logger = logging.getLogger(__name__)

_FORMAT_ALIASES = {
    "xls": "xlsx",
    "spss": "spss_labels",
    "labels": "spss_labels",
}


def normalize_export_format(fmt: str) -> str:
    value = (fmt or "xlsx").lower().strip()
    return _FORMAT_ALIASES.get(value, value)


def record_data_export(*, user, form, export_format: str) -> None:
    """Best-effort log of a successful download. Never raises to the caller."""
    try:
        DataExportEvent.objects.create(
            user=user if getattr(user, "is_authenticated", False) else None,
            form=form,
            export_format=normalize_export_format(export_format),
        )
    except Exception:
        logger.exception("Failed to record data export event")
