"""the ticket data tool."""
from pathlib import Path
import pandas as pd

TICKETS = Path(__file__).resolve().parent.parent / "data/ticket_volume.csv"


def load_tickets(path=TICKETS):
    return pd.read_csv(path, parse_dates=["date"]).set_index("date").sort_index()["tickets"]


def weekly_change(series, start_date, end_date):
    #compares the 7 days ending on each date, since single days swing with the weekend
    try:
        start, end = pd.to_datetime(start_date), pd.to_datetime(end_date)
    except (ValueError, TypeError):
        return "Dates must look like YYYY-MM-DD."
    if start > end:
        return "The start date has to come before the end date."
    if start < series.index.min() + pd.Timedelta(days=6) or end > series.index.max():
        return f"I have data for {series.index.min().date()} through {series.index.max().date()}, and need 7 days before the start date."
    a = int(series.loc[start - pd.Timedelta(days=6):start].sum())
    b = int(series.loc[end - pd.Timedelta(days=6):end].sum())
    return f"Tickets in the 7 days ending {start.date()}: {a}. Ending {end.date()}: {b}. Change: {b - a:+d} ({(b - a) / a * 100:+.1f}%)."
