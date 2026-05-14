"""
Creates the tickets table and seeds it with sample data.
Run from the backend/ directory: python scripts/seed_db.py
"""
import asyncio
import os
import sys

# asyncpg requires SelectorEventLoop on Windows (ProactorEventLoop is incompatible)
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from app.config import settings
from app.database import Base
from app.models import Ticket

DATABASE_URL = (
    f"postgresql+asyncpg://{settings.DB_USER}:{settings.DB_PASSWORD}"
    f"@{settings.DB_HOST}:{settings.DB_PORT}/{settings.DB_NAME}"
)

SAMPLE_TICKETS = [
    {
        "title": "Login page not responding after password reset",
        "description": (
            "After performing a password reset via the email link, users are unable to log in. "
            "The login page loads but submitting the form results in a 500 Internal Server Error. "
            "This affects all users who reset their passwords in the last 24 hours — approximately "
            "47 users have reported this issue. The browser console shows a 'CSRF token mismatch' error. "
            "The problem started immediately after the deployment on 2024-01-15 at 18:30 UTC. "
            "Rolling back the deployment is not possible as it included critical security patches."
        ),
        "status": "open",
    },
    {
        "title": "Invoice #4521 shows incorrect charge amount",
        "description": (
            "Customer John Doe (account #12345) reports that invoice #4521 dated January 10, 2024 "
            "shows a charge of $1,250 instead of the agreed contract price of $950. The customer "
            "provided a signed contract clearly showing the correct pricing tier. The billing team "
            "has been notified and is investigating whether this is an isolated data entry error or "
            "a systematic pricing bug affecting other enterprise accounts. A credit note is pending "
            "approval from the Finance manager."
        ),
        "status": "in_progress",
    },
    {
        "title": "New employee access request — project management tools",
        "description": (
            "New employee Sarah Chen (sarah.chen@company.com), joining the Product team on January 8, 2024, "
            "needs access to Jira and Confluence. Manager approval received from Tom Williams. "
            "Required permissions: Jira — Developer access to PROJECT-ALPHA and PROJECT-BETA boards; "
            "Confluence — Read/write access to the Product space and Engineering wiki. "
            "Access was provisioned successfully and confirmed by the user on January 8."
        ),
        "status": "resolved",
    },
    {
        "title": "Marketing team not receiving email notifications",
        "description": (
            "Multiple users in the Marketing department stopped receiving system email notifications "
            "starting January 12, 2024. This affects password reset emails, task assignment notifications, "
            "and weekly digest emails. All affected users have confirmed emails are not in their spam folders. "
            "The issue appears isolated to accounts with @marketing.company.com addresses — other email "
            "domains are unaffected. The Postmark delivery dashboard shows emails are being sent but "
            "are bouncing with error code 550 (mailbox unavailable). Suspecting a DNS/MX record issue "
            "after the domain migration."
        ),
        "status": "open",
    },
    {
        "title": "Analytics dashboard taking 30+ seconds to load",
        "description": (
            "The main analytics dashboard is experiencing severe performance degradation since the data "
            "warehouse migration on January 11, 2024. Load times have increased from approximately 2 seconds "
            "to over 30 seconds. The issue is most severe for accounts with more than 10,000 records. "
            "Database query logs show the summary aggregation query is performing a full table scan "
            "instead of using the created_at index. This appears to be caused by a missing index that "
            "was not migrated. Temporary workaround: users can access individual report pages which load normally. "
            "Fix is being tested in staging."
        ),
        "status": "in_progress",
    },
    {
        "title": "CSV export silently fails for datasets over 10,000 rows",
        "description": (
            "The export-to-CSV feature fails silently when the selected dataset contains more than 10,000 rows. "
            "The download button shows a spinner for approximately 30 seconds, then resets without producing "
            "any file or error message. Browser network tab shows a 504 Gateway Timeout. Smaller exports "
            "under 10,000 rows work correctly. This is blocking the Finance team from completing their "
            "monthly reconciliation report due January 20. The issue likely stems from the export being "
            "handled synchronously in the request cycle rather than as a background job."
        ),
        "status": "open",
    },
    {
        "title": "Two-factor authentication codes rejected after phone replacement",
        "description": (
            "User Michael Rodriguez (michael.r@company.com) replaced his work phone and re-enrolled in "
            "2FA using Google Authenticator. The QR code scan appeared successful, but all generated "
            "TOTP codes are consistently rejected at login. IT confirmed the authentication server time "
            "is correctly synchronized (NTP verified). Root cause identified: the user's authenticator "
            "app had accumulated a 90-second time drift. Issue resolved by switching to manual key entry "
            "and enabling time-based synchronization in the authenticator app settings."
        ),
        "status": "resolved",
    },
    {
        "title": "Salesforce integration hitting daily API rate limit",
        "description": (
            "The Salesforce integration service is exhausting its 10,000 API calls/day limit by 2 PM each day, "
            "causing all afternoon data sync jobs to fail. Investigation revealed the sync job fetches all "
            "records every 15 minutes instead of using incremental sync with the LastModifiedDate filter. "
            "This results in ~9,600 unnecessary API calls per day. Engineering has written the fix "
            "(replacing bulk fetch with delta sync) and it's ready for deployment. However, the change "
            "requires a 4-hour maintenance window to safely migrate existing sync state. Pending scheduling "
            "with the DevOps team and customer notification."
        ),
        "status": "in_progress",
    },
    {
        "title": "File upload component broken in Safari 17",
        "description": (
            "Users on Safari 17 (macOS Sonoma) cannot upload files through the document management portal. "
            "The file picker opens correctly but after selecting a file, the upload progress bar appears "
            "briefly then disappears without completing. No error is shown to the user. The browser console "
            "shows 'TypeError: Failed to construct FormData: parameter 1 is not of type Blob'. "
            "Chrome and Firefox users are unaffected. This appears to be a Safari 17 breaking change in "
            "how it handles File objects in FormData. Affects approximately 23% of our user base based on "
            "analytics data."
        ),
        "status": "open",
    },
    {
        "title": "Scheduled report emails arriving 6 hours late",
        "description": (
            "All scheduled weekly report emails that should be delivered at 08:00 local time are arriving "
            "around 14:00 instead. This started on January 13, 2024 after the infrastructure was migrated "
            "to a new region. Investigation found that the cron job scheduler is still configured to UTC+0 "
            "but the new servers run in UTC+6. The scheduler configuration was not updated as part of the "
            "migration runbook. Fix is simple (update TZ environment variable in the scheduler service) "
            "but requires a deployment. Scheduled for tonight's maintenance window."
        ),
        "status": "resolved",
    },
]


async def main():
    engine = create_async_engine(DATABASE_URL, connect_args={"ssl": False})

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        print("Schema created (or already exists).")

        result = await conn.execute(text("SELECT COUNT(*) FROM tickets"))
        count = result.scalar()
        if count > 0:
            print(f"Database already contains {count} tickets. Skipping seed.")
            await engine.dispose()
            return

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        for data in SAMPLE_TICKETS:
            session.add(Ticket(**data))
        await session.commit()
        print(f"Seeded {len(SAMPLE_TICKETS)} sample tickets.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(main())
