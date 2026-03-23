# OSC Control from Action Menu
# osc-radial.py
# Lets you control OBS using OSC messages sent from VRChat, such as from the Action Menu.
# (c) 2026 MissingNO123

import obspython as S #type:ignore
import time

from vrchat_oscquery.threaded import vrc_osc
from vrchat_oscquery.common import vrc_client, dict_to_dispatcher

from random import randint
instance = randint(11111, 99999) # Used to differentiate multiple instances of the script running at the same time, because sometimes OBS is really funny with it


#region Parameters
DEFAULT_RECORDING_PARAM = "OBSCtrl_Recording"
DEFAULT_RECORDING_PAUSED_PARAM = "OBSCtrl_RecordingPaused"
DEFAULT_REPLAY_BUFFER_PARAM = "OBSCtrl_ReplayBuffer"
DEFAULT_REPLAY_BUFFER_SAVE_PARAM = "OBSCtrl_SaveReplayBuffer"
DEFAULT_STREAMING_PARAM = "OBSCtrl_Streaming"
DEFAULT_SCENE_PARAM = "OBSCtrl_Scene"

recording_param = DEFAULT_RECORDING_PARAM
recording_paused_param = DEFAULT_RECORDING_PAUSED_PARAM
replay_buffer_param = DEFAULT_REPLAY_BUFFER_PARAM
replay_buffer_save_param = DEFAULT_REPLAY_BUFFER_SAVE_PARAM
streaming_param = DEFAULT_STREAMING_PARAM

MAX_SCENE_SLOTS = 32
num_scenes = 1
scene_list = []
scene_param = DEFAULT_SCENE_PARAM
#endregion


#region OSC
client = vrc_client()
osc_server = None
dispatcher = None

last_tick = 0
LAST_TICK_THRESHOLD = 0.1


def _build_dispatcher_map():
    """ Maps the parameter names to dispatcher callbacks """
    return {
        f"/avatar/parameters/{param}": onOBSCtrlMessageReceived for param in [
            recording_param,
            recording_paused_param,
            replay_buffer_param,
            replay_buffer_save_param,
            streaming_param,
            scene_param
        ]
    }


def _start_osc_server():
    # print("Starting OSC server..." + f"(instance {instance})")
    global osc_server, dispatcher
    dispatcher = dict_to_dispatcher(_build_dispatcher_map())
    osc_server = vrc_osc("OBS OSC Param Receiver " + str(instance), dispatcher)
    time.sleep(1)
    while not osc_server.socket:
        # Wait for VRChat to connect first
        time.sleep(1)


# def _restart_osc_server_if_running():
#     global osc_server
#     if osc_server is None:
#         return

#     if osc_server.shutdown:
#         osc_server.shutdown()
#     osc_server = None
#     _start_osc_server()


def dispatcher_unmap_all(dispatcher):
    """ Unmaps all routes from the dispatcher """
    # print("Unmapping all dispatcher routes..." + f"(instance {instance})")
    if dispatcher is None:
        return

    # pythonosc Dispatcher stores handlers in an internal map of address -> [Handler].
    # Clearing this map removes all route bindings at once.
    if hasattr(dispatcher, "_map"):
        dispatcher._map.clear()

    # Also clear any default handler to avoid stale fallback behavior.
    if hasattr(dispatcher, "set_default_handler"):
        dispatcher.set_default_handler(None)


def reconfigure_dispatcher():
    """ Reconfigures the dispatcher with the current parameter names. Call this after updating parameters. """
    global dispatcher
    if dispatcher is None:
        return

    dispatcher_unmap_all(dispatcher)

    for address, callback in _build_dispatcher_map().items():
        dispatcher.map(address, callback)


def onOBSCtrlMessageReceived(address, value):
    """ Called when the client sends an OSC message that gets matched by the dispatcher """
    if time.time() - last_tick < LAST_TICK_THRESHOLD:
        return
    address = address[address.rfind("/") + 1:]
    # print(f"Received OSC message: {address} = {value} (instance {instance})")
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
    elif address == scene_param:
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            return
        if isinstance(value, float) and not value.is_integer():
            return
        _switch_to_scene_index(int(value))


def poll_frontend_status_callback():
    """ Periodically polls the OBS frontend status and syncs it to VRChat """
    global client, last_tick
    if osc_server is None or not osc_server.socket:
        return
    
    # Replay Buffer Active
    if S.obs_frontend_replay_buffer_active():
        # print("Replay buffer is active.")
        client.send_message(f'/avatar/parameters/{replay_buffer_param}', (True,))
    else: 
        client.send_message(f'/avatar/parameters/{replay_buffer_param}', (False,))

    # Recording Active
    if S.obs_frontend_recording_active():
        # print("Recording is active.")
        client.send_message(f'/avatar/parameters/{recording_param}', (True,))
    else:
        client.send_message(f'/avatar/parameters/{recording_param}', (False,))
    
    # Recording Paused
    if S.obs_frontend_recording_paused():
        # print("Recording is paused.")
        client.send_message(f'/avatar/parameters/{recording_paused_param}', (True,))
    else:
        client.send_message(f'/avatar/parameters/{recording_paused_param}', (False,))
    
    # Streaming Active
    if S.obs_frontend_streaming_active():
        # print("Streaming is active.")
        client.send_message(f'/avatar/parameters/{streaming_param}', (True,))
    else:
        client.send_message(f'/avatar/parameters/{streaming_param}', (False,))

    # Scene Index (1-based): send 0 when the active scene is not in the configured list.
    scene_index = 0
    current_scene = S.obs_frontend_get_current_scene()
    if current_scene:
        try:
            current_scene_name = S.obs_source_get_name(current_scene)
            for i, configured_scene_name in enumerate(scene_list, start=1):
                if configured_scene_name == current_scene_name:
                    scene_index = i
                    break
        finally:
            S.obs_source_release(current_scene)

    client.send_message(f'/avatar/parameters/{scene_param}', (scene_index,))

    last_tick = time.time()


#endregion


#region OBS Functions
def _set_obs_scene(scene_name):
    # print(f"Switching to scene: {scene_name}" + f"(instance {instance})")
    if not scene_name:
        return False

    scenes = S.obs_frontend_get_scenes()
    found = False
    for scene in scenes:
        if S.obs_source_get_name(scene) == scene_name:
            S.obs_frontend_set_current_scene(scene)
            found = True
            break
    S.source_list_release(scenes)
    return found


def _switch_to_scene_index(index):
    # Index values are 1-based
    if index <= 0 or index > len(scene_list):
        return

    scene_name = scene_list[index - 1]
    if not scene_name:
        return

    if not _set_obs_scene(scene_name):
        # print(f"Configured scene for index {index} was not found in OBS: {scene_name}")
        pass


def _set_scene_slot_visibility(props, count):
    """ Shows or hides scene selection properties based on the number of scenes configured. """
    for i in range(1, MAX_SCENE_SLOTS + 1):
        scene_prop = S.obs_properties_get(props, f"scene_{i}")
        if scene_prop is not None:
            S.obs_property_set_visible(scene_prop, i <= count)


def _on_num_scenes_modified(props, prop, settings):
    """ Script Properties callback for when number of scenes is modified """
    count = S.obs_data_get_int(settings, "num_scenes")
    count = max(1, min(MAX_SCENE_SLOTS, count))
    _set_scene_slot_visibility(props, count)
    return True


#endregion


#region OBS Script API
def script_defaults(settings):
    S.obs_data_set_default_string(settings, "recording_param", DEFAULT_RECORDING_PARAM)
    S.obs_data_set_default_string(settings, "recording_paused_param", DEFAULT_RECORDING_PAUSED_PARAM)
    S.obs_data_set_default_string(settings, "replay_buffer_param", DEFAULT_REPLAY_BUFFER_PARAM)
    S.obs_data_set_default_string(settings, "replay_buffer_save_param", DEFAULT_REPLAY_BUFFER_SAVE_PARAM)
    S.obs_data_set_default_string(settings, "streaming_param", DEFAULT_STREAMING_PARAM)
    S.obs_data_set_default_string(settings, "scene_param", DEFAULT_SCENE_PARAM)
    S.obs_data_set_default_int(settings, "num_scenes", 1)


def script_update(settings):
    global recording_param, recording_paused_param
    global replay_buffer_param, replay_buffer_save_param
    global streaming_param, scene_param, num_scenes, scene_list

    old_params = (
        recording_param,
        recording_paused_param,
        replay_buffer_param,
        replay_buffer_save_param,
        streaming_param,
        scene_param,
    )

    recording_param = S.obs_data_get_string(settings, "recording_param").strip() or DEFAULT_RECORDING_PARAM
    recording_paused_param = S.obs_data_get_string(settings, "recording_paused_param").strip() or DEFAULT_RECORDING_PAUSED_PARAM
    replay_buffer_param = S.obs_data_get_string(settings, "replay_buffer_param").strip() or DEFAULT_REPLAY_BUFFER_PARAM
    replay_buffer_save_param = S.obs_data_get_string(settings, "replay_buffer_save_param").strip() or DEFAULT_REPLAY_BUFFER_SAVE_PARAM
    streaming_param = S.obs_data_get_string(settings, "streaming_param").strip() or DEFAULT_STREAMING_PARAM
    scene_param = S.obs_data_get_string(settings, "scene_param").strip() or DEFAULT_SCENE_PARAM

    num_scenes = S.obs_data_get_int(settings, "num_scenes")
    num_scenes = max(1, min(MAX_SCENE_SLOTS, num_scenes))
    S.obs_data_set_int(settings, "num_scenes", num_scenes)

    updated_scene_list = []
    for i in range(1, num_scenes + 1):
        updated_scene_list.append(S.obs_data_get_string(settings, f"scene_{i}"))
    scene_list = updated_scene_list

    new_params = (
        recording_param,
        recording_paused_param,
        replay_buffer_param,
        replay_buffer_save_param,
        streaming_param,
        scene_param,
    )

    if old_params != new_params:
        reconfigure_dispatcher()


def script_save(settings):
    """Persist script settings explicitly to avoid losing indexed scene mappings."""
    S.obs_data_set_string(settings, "recording_param", recording_param)
    S.obs_data_set_string(settings, "recording_paused_param", recording_paused_param)
    S.obs_data_set_string(settings, "replay_buffer_param", replay_buffer_param)
    S.obs_data_set_string(settings, "replay_buffer_save_param", replay_buffer_save_param)
    S.obs_data_set_string(settings, "streaming_param", streaming_param)
    S.obs_data_set_string(settings, "scene_param", scene_param)
    S.obs_data_set_int(settings, "num_scenes", num_scenes)

    for i in range(1, MAX_SCENE_SLOTS + 1):
        if i <= len(scene_list):
            scene_name = scene_list[i - 1]
        else:
            scene_name = S.obs_data_get_string(settings, f"scene_{i}")
        S.obs_data_set_string(settings, f"scene_{i}", scene_name)


def script_load(settings):
    script_update(settings)
    _start_osc_server()

    S.timer_add(poll_frontend_status_callback, 997)

    # S.obs_frontend_add_event_callback(on_replay_buffer_saved)


def script_unload():
    global osc_server, dispatcher
    S.timer_remove(poll_frontend_status_callback)
    dispatcher_unmap_all(dispatcher)
    # print("Shutting down the OSC server...")
    if osc_server and osc_server.shutdown:
        osc_server.shutdown()
    dispatcher = None
    osc_server = None

# def on_replay_buffer_saved(event):
#     if event == S.OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED:
#         client.send_message('/avatar/parameters/OBSCtrl_ReplayBufferSaved', (False,))


def script_properties():
    props = S.obs_properties_create()

    S.obs_properties_add_text(props, "recording_param", "Recording Parameter", S.OBS_TEXT_DEFAULT)
    S.obs_properties_add_text(props, "recording_paused_param", "Recording Paused Parameter", S.OBS_TEXT_DEFAULT)
    S.obs_properties_add_text(props, "replay_buffer_param", "Replay Buffer Parameter", S.OBS_TEXT_DEFAULT)
    S.obs_properties_add_text(props, "replay_buffer_save_param", "Replay Buffer Save Parameter", S.OBS_TEXT_DEFAULT)
    S.obs_properties_add_text(props, "streaming_param", "Streaming Parameter", S.OBS_TEXT_DEFAULT)
    S.obs_properties_add_text(props, "scene_param", "Scene Parameter Name", S.OBS_TEXT_DEFAULT)

    num_scenes_prop = S.obs_properties_add_int(
        props,
        "num_scenes",
        "Number of Indexed Scenes",
        1,
        MAX_SCENE_SLOTS,
        1
    )
    S.obs_property_set_modified_callback(num_scenes_prop, _on_num_scenes_modified)

    scenes = S.obs_frontend_get_scenes()
    scene_names = [S.obs_source_get_name(scene) for scene in scenes]
    S.source_list_release(scenes)

    for i in range(1, MAX_SCENE_SLOTS + 1):
        scene_prop = S.obs_properties_add_list(
            props,
            f"scene_{i}",
            f"Scene {i}",
            S.OBS_COMBO_TYPE_EDITABLE,
            S.OBS_COMBO_FORMAT_STRING,
        )
        for name in scene_names:
            S.obs_property_list_add_string(scene_prop, name, name)

    _set_scene_slot_visibility(props, num_scenes)

    return props


def script_description():
    print("script_description" + str(instance))
    return """Control OBS using OSC messages sent from VRChat.
    Configure the parameter names that VRChat will send for different OBS actions, and optionally configure up to 32 scene names to be indexed for quick switching from VRChat."""


#endregion

# C:\Program Files\obs-studio\data\obs-plugins\frontend-tools\scripts

# OBS_FRONTEND_EVENT_REPLAY_BUFFER_SAVED
# Triggered when the replay buffer has been saved.