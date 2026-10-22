"""Automatic group membership from e-mail patterns (``auto_groups`` in settings.yaml)."""
import logging
import re

from django.contrib.auth.models import Group
from django.db import transaction

from core import config
from core.permissions import ADMIN_GROUP

logger = logging.getLogger('cloudgene.auth')


def match_auto_groups(email: str, rules: list[dict] | None = None) -> tuple[list[int], list[str]]:
    """Indexes of the rules whose pattern fully matches ``email``, and the union of their
    groups (``admin`` removed). ``rules`` defaults to the saved ``auto_groups``."""
    if rules is None:
        rules = config.get('auto_groups') or []
    indexes: list[int] = []
    names: dict[str, None] = {}
    for i, rule in enumerate(rules):
        pattern = rule.get('pattern')
        if not pattern or not re.fullmatch(pattern, email, re.IGNORECASE):
            continue
        indexes.append(i)
        for name in rule.get('groups') or []:
            if name.lower() != ADMIN_GROUP.lower():
                names[name] = None
    return indexes, list(names)


def matching_group_names(email: str, rules: list[dict] | None = None) -> list[str]:
    """Union of the groups of every rule whose pattern fully matches ``email``."""
    return match_auto_groups(email, rules)[1]


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
