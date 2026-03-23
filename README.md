# OBS Scripts for VRChat

A collection of OBS Studio scripts that provide extra functionality and integration with VRChat. These can be added directly to OBS Studio via the Scripts menu and do not require running an external application. All scripts are made to run on Windows and Linux.

See the individual headings for details of each script.

- [VRC Loading Screen Scene Switcher](#vrc-loading-screen-scene-switcher)
- [OSC Control from Action Menu](#osc-control-from-action-menu)

<!-- An OBS Studio script that automatically switches to a scene when entering a loading screen in VRChat, and switches it back when done. 
Destination scene can be whatever you want, see Demo below for an example.
Suports Windows and Linux (Proton) out of the box. -->

## Requirements
- Python 3 installed and added to PATH (on Windows, ensure the "Add Python 3.x to PATH" option is checked during installation).
- OBS Studio

## Installation
1. Download this repository using the **Code > Download  ZIP** button, then unzip the files to somewhere on your PC.
1. Alternatively, right-click on the download button on this page for any individual script, and click "Save As".
1. In OBS Studio, go to Tools > Scripts.
1. Click the "+" button and add the `.py` files you just downloaded.
1. Configure each script's settings from its properties panel.

# VRC Loading Screen Scene Switcher

Automatically switches to a scene when entering the loading screen in VRChat, then switches back when done. 
The destination scenes can also be set to whatever you want, see demo below for an example. 

### [Download Script](https://raw.githubusercontent.com/MissingNO123/OBS-VRCLoad-Sceneswitcher/refs/heads/main/vrcload-sceneswitcher.py) (Right-click > Save As)

### Usage
0. Make sure Logging is enabled in VRChat!
1. Set the "Loading" and "Default" scenes to switch to. There is an option to automatically return to the last scene you had active before entering the loading screen.
2. Optionally, set the path to the folder your VRChat logs are output to. This is automatically set to the default directory based on your OS and is only needed on unique setups that output logs to a different folder.
3. Optionally, change the update interval for how often it reads the log file.
4. The script will listen for VRChat log events and automatically switch scenes.
5. You can disable it using the checkbox in the script's properties.

### Demo
https://github.com/user-attachments/assets/74e36e11-0b14-4299-9628-157dfd953cda


# OSC Control from Action Menu

Reacts to avatar parameters changing and sends control commands to OBS. Meant to be used with the Action Menu, but can be triggered from anything on the avatar.
The script will also sync the current status of recording/streaming/replay buffer and active scene back to VRChat so you can also check its state from the Action Menu.

By default, it responds to the following parameters:

| Parameter                | Type | Action                        |
|--------------------------|------|-------------------------------|
| OBSCtrl_Recording        | Bool | Start/Stop Recording          |
| OBSCtrl_RecordingPaused  | Bool | Pause Current Recording       |
| OBSCtrl_ReplayBuffer     | Bool | Start/Stop Replay Buffer      |
| OBSCtrl_SaveReplayBuffer | Bool | Save Current Replay Buffer    |
| OBSCtrl_Streaming        | Bool | Start/Stop Streaming          |
| OBSCtrl_Scene            | Int  | Switch to scene # from a List |

### [Download Script](https://raw.githubusercontent.com/MissingNO123/OBS-VRCLoad-Sceneswitcher/refs/heads/main/osc-radial.py) (Right-click > Save As)
### [Download Modular Avatar Prefab](https://github.com/MissingNO123/OBS-Scripts-for-VRChat/raw/refs/heads/main/OBS%20Control%20Menu%20-%20MODULAR%20AVATAR.unitypackage) (Right-click > Save As)

### Usage
0. Make sure OSC is enabled in VRChat!
1. Set up your avatar with the required parameters (or use the provided MA prefab)
2. In the script properties, set:
	- Number of Indexed Scenes
	- Scene Names for each index 
3. When any configured parameter's value changes, the corresponding action will be taken in OBS.
4. Set the Scene parameter to a number and it will switch to that numbered scene out of the list configured in the script settings window

### Demo
(soon)