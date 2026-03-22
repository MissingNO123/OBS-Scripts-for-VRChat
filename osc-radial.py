# OSC Control from Action Menu
# osc-radial.py
# Lets you control OBS using OSC messages sent from VRChat, such as from the Action Menu.
# (c) 2026 MissingNO123

import obspython as S #type:ignore
import threading
import time

from vrchat_oscquery.threaded import vrc_osc
from vrchat_oscquery.common import vrc_client, dict_to_dispatcher

#region Parameter Names
recording_param = "OBSCtrl_Recording"
recording_paused_param = "OBSCtrl_RecordingPaused"
replay_buffer_param = "OBSCtrl_ReplayBuffer"
replay_buffer_save_param = "OBSCtrl_SaveReplayBuffer"
streaming_param = "OBSCtrl_Streaming"
#endregion

#region OSCQuery
client = vrc_client()
osc_server = None

last_tick = 0

def onOBSCtrlMessageReceived(address, value):
    """Called when the client changes their emote."""
    if time.time() - last_tick < 0.1:
        return
    address = address[address.rfind("/") + 1:]
    print(f"Received OSC message: {address} = {value}")
    if address == replay_buffer_param:
        if value:
            S.obs_frontend_replay_buffer_start()
        else:
            S.obs_frontend_replay_buffer_stop()
    
    elif address == recording_param:
        if value:
            S.obs_frontend_recording_start()
        else:
            S.obs_frontend_recording_stop()
    
    elif address == recording_paused_param:
        if not S.obs_frontend_recording_active():
            return
        if value:
            S.obs_frontend_recording_pause(True)
        else:
            S.obs_frontend_recording_pause(False)
    
    elif address == streaming_param:
        if value:
            S.obs_frontend_streaming_start()
        else:
            S.obs_frontend_streaming_stop()
    
    elif address == replay_buffer_save_param:
        if value:
            S.obs_frontend_replay_buffer_save()
#endregion


#region OBS Script API
def script_defaults(settings):
    pass


def script_update(settings):
    pass


def script_load(settings):
    global osc_server
    osc_server = vrc_osc("OBS OSC Param Receiver", dict_to_dispatcher({
        f"/avatar/parameters/{param}": onOBSCtrlMessageReceived for param in [
            recording_param,
            recording_paused_param,
            replay_buffer_param,
            replay_buffer_save_param,
            streaming_param
        ]
    }))
    time.sleep(1)
    while not osc_server.socket:
        # Wait for VRChat to connect first
        time.sleep(1)

    S.timer_add(check_state_cb, 997)

    # S.obs_frontend_add_event_callback(on_replay_buffer_saved)



def script_unload():
    global osc_server
    S.timer_remove(check_state_cb)
    print("Shutting down the OSC server...")
    if osc_server.shutdown:
        osc_server.shutdown()

# def on_replay_buffer_saved(event):
#     if event == S.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED:
#         client.send_message('/avatar/parameters/OBSCtrl_ReplayBufferSaved', (False,))

def check_state_cb():
    global client, last_tick
    if osc_server is None or not osc_server.socket:
        return
    
    # Replay Buffer Active
    if S.obs_frontend_replay_buffer_active():
        # print("Replay buffer is active.")
        client.send_message('/avatar/parameters/OBSCtrl_ReplayBuffer', (True,))
    else: 
        client.send_message('/avatar/parameters/OBSCtrl_ReplayBuffer', (False,))

    # Recording Active
    if S.obs_frontend_recording_active():
        # print("Recording is active.")
        client.send_message('/avatar/parameters/OBSCtrl_Recording', (True,))
    else:
        client.send_message('/avatar/parameters/OBSCtrl_Recording', (False,))
    
    # Recording Paused
    if S.obs_frontend_recording_paused():
        # print("Recording is paused.")
        client.send_message('/avatar/parameters/OBSCtrl_RecordingPaused', (True,))
    else:
        client.send_message('/avatar/parameters/OBSCtrl_RecordingPaused', (False,))
    
    # Streaming Active
    if S.obs_frontend_streaming_active():
        # print("Streaming is active.")
        client.send_message('/avatar/parameters/OBSCtrl_Streaming', (True,))
    else:
        client.send_message('/avatar/parameters/OBSCtrl_Streaming', (False,))

    last_tick = time.time()

def script_properties():
    props = S.obs_properties_create()

    return props


def script_description():
    return """Controls OBS using OSC messages sent from VRChat. 
    "Supported parameters: 
    "OBSCtrl_ReplayBuffer (bool) - Start/Stop the replay buffer
    "OBSCtrl_SaveReplayBuffer (bool) - Save the replay buffer.
    "OBSCtrl_Recording (bool) - Start/Stop recording.
    "OBSCtrl_RecordingPaused (bool) - Pause/Unpause recording
    "OBSCtrl_Streaming (bool) - Start/Stop streaming
"""

#endregion

# C:\Program Files\obs-studio\data\obs-plugins\frontend-tools\scripts

# OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED
# Triggered when the replay buffer has been saved.