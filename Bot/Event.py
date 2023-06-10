import datetime

class Event:
    last_checked: datetime
    recent_note: str | int | bool
    event_name: str
    param: str | None
    channel_ids: list[int]
    user_ids: list[int]

    def __init__(self, datetime_float, event, param, channel_ids, user_ids, note) -> None:
        self.last_checked = datetime.datetime.fromtimestamp(datetime_float)
        self.recent_note = note
        self.event_name = event
        self.param = param
        self.channel_ids = channel_ids
        self.user_ids = user_ids
    
    def get_dict(self):
        obj = {}
        obj['last_checked'] = datetime.datetime.timestamp(self.last_checked)
        obj['event'] = self.event_name
        obj['param'] = self.param if self.param != None else ''
        obj['latest'] = self.recent_note
        obj['channels'] = self.channel_ids
        obj['users'] = self.user_ids
        return obj
    
    def get_timestamp(self):
        return self.last_checked.datetime.timestamp()
    
    def __str__(self) -> str:
        return f'Event `{self.event_name}` with param `{self.param}`, {len(self.channel_ids)} channel subs and {len(self.user_ids)} user subs'