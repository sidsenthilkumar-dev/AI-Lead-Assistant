import sqlite3
from pathlib import Path

from data.models import Lead


DATABASE_PATH = Path("leads.db")


def get_connection():
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT DEFAULT '',
            company TEXT NOT NULL,
            industry TEXT DEFAULT '',
            website TEXT DEFAULT '',
            phone TEXT DEFAULT '',
            address TEXT DEFAULT '',
            source TEXT DEFAULT '',

            problem TEXT DEFAULT '',
            qualification TEXT DEFAULT '',
            score INTEGER,

            status TEXT DEFAULT 'New',

            outreach_message TEXT DEFAULT '',
            follow_up_message TEXT DEFAULT '',
            next_action TEXT DEFAULT ''
        )
        """
    )

    connection.commit()
    connection.close()


def add_lead(lead: Lead):
    connection = get_connection()

    cursor = connection.execute(
        """
        INSERT INTO leads (
            name,
            company,
            industry,
            website,
            phone,
            address,
            source,
            problem,
            qualification,
            score,
            status,
            outreach_message,
            follow_up_message,
            next_action
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            lead.name,
            lead.company,
            lead.industry,
            lead.website,
            lead.phone,
            lead.address,
            lead.source,
            lead.problem,
            lead.qualification,
            lead.score,
            lead.status,
            lead.outreach_message,
            lead.follow_up_message,
            lead.next_action,
        ),
    )

    connection.commit()

    lead_id = cursor.lastrowid

    connection.close()

    return lead_id


def get_leads():
    connection = get_connection()

    rows = connection.execute(
        """
        SELECT *
        FROM leads
        ORDER BY id DESC
        """
    ).fetchall()

    connection.close()

    return [dict(row) for row in rows]


def update_lead(lead_id: int, **fields):
    if not fields:
        return

    allowed_fields = {
        "name",
        "company",
        "industry",
        "website",
        "phone",
        "address",
        "source",
        "problem",
        "qualification",
        "score",
        "status",
        "outreach_message",
        "follow_up_message",
        "next_action",
    }

    fields = {
        key: value
        for key, value in fields.items()
        if key in allowed_fields
    }

    if not fields:
        return

    assignments = ", ".join(
        f"{key} = ?" for key in fields
    )

    values = list(fields.values())
    values.append(lead_id)

    connection = get_connection()

    connection.execute(
        f"""
        UPDATE leads
        SET {assignments}
        WHERE id = ?
        """,
        values,
    )

    connection.commit()
    connection.close()