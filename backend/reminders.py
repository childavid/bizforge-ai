"""Background delivery of due BizForge schedule reminders."""

import logging

from database.db import get_due_schedule_reminders, init_db, mark_schedule_reminded
from utils.notifications import notify_schedule_due


logger = logging.getLogger(__name__)


def deliver_due_schedule_reminders(limit=100):
    """Send each queued schedule reminder once; safe to run every five minutes."""
    init_db()
    sent = 0
    pending = 0
    for schedule in get_due_schedule_reminders(limit=limit):
        delivered = notify_schedule_due(
            schedule["email"],
            schedule["title"],
            schedule["due_at"],
            schedule["timezone"],
            schedule.get("notes", ""),
        )
        if delivered and mark_schedule_reminded(schedule["id"]):
            sent += 1
        else:
            pending += 1
    logger.info("Schedule reminder run complete: sent=%s pending=%s", sent, pending)
    return {"sent": sent, "pending": pending}


if __name__ == "__main__":
    print(deliver_due_schedule_reminders())
