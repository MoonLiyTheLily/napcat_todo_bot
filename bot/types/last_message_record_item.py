class LastMessageRecordItem:
    """
    最近消息记录项
    """

    def __init__(self, user_id: str, send_time: str):
        self.user_id = user_id
        self.send_time: str = send_time
