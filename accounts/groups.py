"""Automatic group membership from e-mail patterns (``auto_groups`` in settings.yaml)."""
import logging
import re

from django.contrib.auth.models import Group
from django.db import transaction

from core import config
from core.permissions import ADMIN_GROUP

logger = logging.getLogger('cloudgene.auth')


def matching_group_names(email: str) -> list[str]:
    """Union of the groups of every rule whose pattern fully matches ``email``."""
    names: dict[str, None] = {}
    for rule in config.get('auto_groups') or []:
        pattern = rule.get('pattern')
        if not pattern or not re.fullmatch(pattern, email, re.IGNORECASE):
            continue
        for name in rule.get('groups') or []:
            if name.lower() != ADMIN_GROUP.lower():
                names[name] = None
    return list(names)


def apply_auto_groups(user) -> list[str]:
    """Add ``user`` to the groups their e-mail address earns. Additive only; never raises."""
    try:
        names = matching_group_names(user.email)
        with transaction.atomic():
            for name in names:
                group, _ = Group.objects.get_or_create(name=name)
                user.groups.add(group)
    except Exception:
        logger.exception('Auto-assigning groups to %s failed', user.username)
        return []
    if names:
        logger.info('Auto-assigned %s to groups %s', user.username, ', '.join(names))
    return names
