
def now():
    now_dt = datetime.datetime.now(tz=ZoneInfo(os.environ["TZ"])).replace(tzinfo=None).replace(microsecond=0)
    result = now_dt.strftime("%Y-%m-%d %H:%M:%S")
    return now_dt
