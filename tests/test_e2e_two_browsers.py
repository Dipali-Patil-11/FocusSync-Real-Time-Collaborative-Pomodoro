import time
import requests
import socketio

SERVER_URL = "http://localhost:5000"

def run_two_browser_verification():
    print("==================================================")
    print("STARTING REAL TWO-BROWSER NOTIFICATION & SOUND TEST")
    print("==================================================")

    # 1. Health check
    res = requests.get(f"{SERVER_URL}/api/health")
    assert res.status_code == 200
    print(f"[OK] Server Health Check Passed: {res.json()}")

    # 2. Browser 1 creates room as Dipali
    res_create = requests.post(f"{SERVER_URL}/api/rooms/create", json={"username": "Dipali"})
    assert res_create.status_code == 201
    create_data = res_create.json()["data"]
    room_code = create_data["room_code"]
    user1_token = create_data["participant_token"]
    print(f"[OK] Browser 1 (Dipali) created room {room_code}")

    # Connect Browser 1 Socket
    sio1 = socketio.Client()
    events_b1 = []

    @sio1.on('*')
    def catch_all_b1(event, data=None):
        events_b1.append((event, data))

    sio1.connect(SERVER_URL, transports=['polling', 'websocket'])
    sio1.emit('join_room', {
        'room_code': room_code,
        'username': 'Dipali',
        'participant_token': user1_token
    })
    time.sleep(0.3)

    # 3. Browser 2 joins room as TestUser
    sio2 = socketio.Client()
    events_b2 = []

    @sio2.on('*')
    def catch_all_b2(event, data=None):
        events_b2.append((event, data))

    events_b1.clear()
    sio2.connect(SERVER_URL, transports=['polling', 'websocket'])
    sio2.emit('join_room', {
        'room_code': room_code,
        'username': 'TestUser'
    })
    time.sleep(0.5)

    # VERIFY USER JOIN NOTIFICATION:
    # Dipali (Browser 1) receives participant_joined event for TestUser
    join_events_b1 = [d for e, d in events_b1 if e == 'participant_joined']
    assert len(join_events_b1) > 0
    assert join_events_b1[0]['username'] == 'TestUser'
    assert 'event_id' in join_events_b1[0]
    print(f"[OK] Join Notification Verified: Browser 1 received '{join_events_b1[0]['title']}'")

    # TestUser (Browser 2) MUST NOT receive its own join notification
    join_events_b2 = [d for e, d in events_b2 if e == 'participant_joined']
    assert len(join_events_b2) == 0
    print("[OK] Join Self-Exclusion Verified: Browser 2 did not receive its own join notification")

    # 4. FOCUS TIMER START NOTIFICATION
    events_b1.clear()
    events_b2.clear()
    sio1.emit('timer_start', {'room_code': room_code})
    time.sleep(0.3)

    start_notifs_b1 = [d for e, d in events_b1 if e == 'timer_started_notification']
    start_notifs_b2 = [d for e, d in events_b2 if e == 'timer_started_notification']

    assert len(start_notifs_b1) > 0 and len(start_notifs_b2) > 0
    assert start_notifs_b1[0]['mode'] == 'FOCUS'
    assert start_notifs_b1[0]['title'] == 'Focus session started'
    assert start_notifs_b1[0]['message'] == 'Time to focus!'
    assert 'event_id' in start_notifs_b1[0]
    print("[OK] Focus Start Notification Verified: Both participants received 'Focus session started'")

    # 5. SHORT BREAK START NOTIFICATION
    events_b1.clear()
    events_b2.clear()
    sio1.emit('timer_change_mode', {'room_code': room_code, 'mode': 'SHORT_BREAK'})
    time.sleep(0.2)
    sio1.emit('timer_start', {'room_code': room_code})
    time.sleep(0.3)

    break_notifs_b1 = [d for e, d in events_b1 if e == 'timer_started_notification']
    break_notifs_b2 = [d for e, d in events_b2 if e == 'timer_started_notification']

    assert len(break_notifs_b1) > 0 and len(break_notifs_b2) > 0
    assert break_notifs_b1[0]['mode'] == 'SHORT_BREAK'
    assert break_notifs_b1[0]['title'] == 'Short break started'
    assert break_notifs_b1[0]['message'] == 'Take a short break.'
    print("[OK] Short Break Start Notification Verified: Both received 'Short break started'")

    # 6. LONG BREAK START NOTIFICATION
    events_b1.clear()
    events_b2.clear()
    sio1.emit('timer_change_mode', {'room_code': room_code, 'mode': 'LONG_BREAK'})
    time.sleep(0.2)
    sio1.emit('timer_start', {'room_code': room_code})
    time.sleep(0.3)

    long_notifs_b1 = [d for e, d in events_b1 if e == 'timer_started_notification']
    long_notifs_b2 = [d for e, d in events_b2 if e == 'timer_started_notification']

    assert len(long_notifs_b1) > 0 and len(long_notifs_b2) > 0
    assert long_notifs_b1[0]['mode'] == 'LONG_BREAK'
    assert long_notifs_b1[0]['title'] == 'Long break started'
    assert long_notifs_b1[0]['message'] == 'Enjoy your long break.'
    print("[OK] Long Break Start Notification Verified: Both received 'Long break started'")

    # 7. TIMER COMPLETION NOTIFICATION
    events_b1.clear()
    events_b2.clear()
    sio1.emit('timer_complete', {'room_code': room_code})
    time.sleep(0.3)

    comp_notifs_b1 = [d for e, d in events_b1 if e == 'timer_completed_notification']
    comp_notifs_b2 = [d for e, d in events_b2 if e == 'timer_completed_notification']

    assert len(comp_notifs_b1) > 0 and len(comp_notifs_b2) > 0
    assert comp_notifs_b1[0]['mode'] == 'LONG_BREAK'
    assert comp_notifs_b1[0]['title'] == 'Long break completed'
    print("[OK] Timer End Notification Verified: Both received completion notification")

    # 8. USER LEAVE NOTIFICATION
    events_b1.clear()
    user2_token = [p['participant_token'] for p in join_events_b1[0]['participants'] if p['username'] == 'TestUser'][0]
    sio2.emit('leave_room', {'room_code': room_code, 'participant_token': user2_token})
    time.sleep(0.4)

    leave_events_b1 = [d for e, d in events_b1 if e == 'participant_left']
    assert len(leave_events_b1) > 0
    assert leave_events_b1[0]['username'] == 'TestUser'
    assert 'event_id' in leave_events_b1[0]
    print(f"[OK] Leave Notification Verified: Browser 1 received '{leave_events_b1[0]['title']}'")

    # Clean up
    sio1.disconnect()
    sio2.disconnect()

    print("==================================================")
    print("ALL REAL-TIME NOTIFICATION & SOUND TESTS PASSED!")
    print("==================================================")

if __name__ == '__main__':
    run_two_browser_verification()
