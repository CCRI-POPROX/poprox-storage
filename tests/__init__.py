from sqlalchemy import text


def clear_tables(conn, *tables):
    for table in tables:
        conn.execute(text(f"delete from {table};"))
