# db/profiling.py
import time

from sqlalchemy import event

from app.db.session.session import engine


query_timings = []  # stores queries per request


def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.perf_counter()


def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.perf_counter() - context._query_start_time
    query_timings.append(
        {
            "statement": statement,
            "parameters": parameters,
            "time": round(total * 1000, 2),  # ms
        }
    )


def setup_query_profiling():
    """Attach event listeners to SQLAlchemy Session."""
    event.listen(engine, "before_cursor_execute", before_cursor_execute)
    event.listen(engine, "after_cursor_execute", after_cursor_execute)
