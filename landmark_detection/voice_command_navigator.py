#!/usr/bin/env python3
import ctypes
from ctypes.util import find_library

# === Suppress ALSA Warnings ===
def py_error_handler(filename, line, function, err, fmt):
    return

ERROR_HANDLER_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_char_p, ctypes.c_int,
                                      ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p)

c_error_handler = ERROR_HANDLER_FUNC(py_error_handler)
asound = ctypes.cdll.LoadLibrary(find_library('asound'))
asound.snd_lib_error_set_handler(c_error_handler)

# === Imports ===
import rospy
import actionlib
import yaml
import speech_recognition as sr
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Quaternion
from tf.transformations import quaternion_from_euler
import os

# Paths to landmarks for each floor
UPSTAIRS_LANDMARKS = "/home/david/habitat_ws/src/image_logger/scripts/upstairs_landmarks.yaml"
DOWNSTAIRS_LANDMARKS = "/home/david/habitat_ws/src/image_logger/scripts/downstairs_landmarks.yaml"

def load_landmarks(filepath):
    if os.path.exists(filepath):
        with open(filepath, "r") as f:
            return yaml.safe_load(f) or {}
    rospy.logwarn(f"No landmarks file found at {filepath}")
    return {}

def navigate_to(client, x, y, yaw):
    rospy.loginfo(f"Navigating to coordinates: x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}")
    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "map"
    goal.target_pose.header.stamp = rospy.Time.now()

    q = quaternion_from_euler(0, 0, yaw)
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.orientation = Quaternion(*q)

    client.send_goal(goal)
    client.wait_for_result()

def listen_for_command(recognizer, microphone):
    with microphone as source:
        recognizer.adjust_for_ambient_noise(source)
        rospy.loginfo("Listening for voice command...")
        try:
            audio = recognizer.listen(source, timeout=3, phrase_time_limit=5)
        except sr.WaitTimeoutError:
            rospy.loginfo("Listening timed out, no speech detected")
            return None
    try:
        command = recognizer.recognize_google(audio).lower()
        rospy.loginfo(f"Recognized speech: '{command}'")
        return command
    except sr.UnknownValueError:
        rospy.logwarn("Could not understand audio")
    except sr.RequestError as e:
        rospy.logerr(f"Speech recognition service error: {e}")
    return None

def main():
    rospy.init_node('voice_command_navigator')
    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)

    rospy.loginfo("Waiting for move_base action server...")
    client.wait_for_server()
    rospy.loginfo("Connected to move_base action server")

    recognizer = sr.Recognizer()
    microphone = sr.Microphone()

    rospy.loginfo("Voice Command Navigator ready. Say commands starting with 'robot'...")

    rate = rospy.Rate(0.5)  # Half Hz, to avoid rapid repeats
    while not rospy.is_shutdown():
        command = listen_for_command(recognizer, microphone)
        if not command:
            rate.sleep()
            continue

        # Activation phrase filter
        if "robot" not in command:
            rospy.loginfo("Activation keyword 'robot' not found; ignoring command.")
            rate.sleep()
            continue

        # Determine floor
        if "upstairs" in command:
            landmarks = load_landmarks(UPSTAIRS_LANDMARKS)
        elif "downstairs" in command:
            landmarks = load_landmarks(DOWNSTAIRS_LANDMARKS)
        else:
            rospy.logwarn("Floor not specified in command; please say 'upstairs' or 'downstairs'.")
            rate.sleep()
            continue

        # Find target landmark in command
        target_name = None
        for name in landmarks.keys():
            if name.lower() in command:
                target_name = name
                break

        if target_name:
            target = landmarks[target_name]
            rospy.loginfo(f"Command recognized: navigating to '{target_name}'")
            navigate_to(client, target['x'], target['y'], target.get('yaw', 0.0))
            rospy.loginfo(f"Arrived at '{target_name}'")
        else:
            rospy.logwarn(f"No matching landmark found in command: '{command}'")
        rate.sleep()

if __name__ == '__main__':
    main()

