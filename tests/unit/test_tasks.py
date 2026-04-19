from tasks.ping import ping

def test_ping_task():
    result = ping.delay()
    assert result.get() == "pong"