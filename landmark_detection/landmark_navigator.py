#!/usr/bin/env python3
import rospy
import actionlib
import yaml
import math
import rospkg
import speech_recognition as sr
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Quaternion
from tf.transformations import quaternion_from_euler

def load_landmarks(filepath):
    try:
        with open(filepath, 'r') as f:
            landmarks = yaml.safe_load(f)
            if not landmarks:
                rospy.logwarn(f"No landmarks found in {filepath}.")
                return {}
            return landmarks
    except Exception as e:
        rospy.logerr(f"Error loading landmarks: {e}")
        return {}

def navigate_to(client, x, y, yaw, target_name):
    rospy.loginfo(f"Navigating to {target_name}: ({x}, {y}, yaw={yaw})...")
    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "map"
    goal.target_pose.header.stamp = rospy.Time.now()

    q = quaternion_from_euler(0, 0, yaw)
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.position.z = 0.0
    goal.target_pose.pose.orientation = Quaternion(*q)

    client.send_goal(goal)
    client.wait_for_result()

    if client.get_state() == actionlib.GoalStatus.SUCCEEDED:
        rospy.loginfo(f"✅ Successfully arrived at {target_name}.")
    else:
        rospy.logwarn(f"⚠️ Failed to reach {target_name}. Goal state: {client.get_state()}")

def listen_for_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        rospy.loginfo("🎤 Say a landmark name...")
        audio = r.listen(source)

    try:
        command = r.recognize_google(audio)
        rospy.loginfo(f"Heard: '{command}'")
        return command.lower()
    except sr.UnknownValueError:
        rospy.logwarn("Could not understand audio")
    except sr.RequestError as e:
        rospy.logerr(f"Speech recognition failed: {e}")

    return None

def main():
    rospy.init_node('voice_command_navigator')
    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    rospy.loginfo("⏳ Waiting for move_base action server...")
    client.wait_for_server()

    # Get landmarks file path
    rospack = rospkg.RosPack()
    landmarks_path = rospack.get_path('image_logger') + '/scripts/landmarks.yaml'
    landmarks = load_landmarks(landmarks_path)
    rospy.loginfo(f"🏁 Available landmarks: {list(landmarks.keys())}")

    rate = rospy.Rate(1)
    while not rospy.is_shutdown():
        command = listen_for_command()
        if command:
            words = command.lower().split()
            target_name = None
            for name in landmarks.keys():
                if name.lower() in words:
                    target_name = name
                    break

            if target_name:
                target = landmarks[target_name]
                navigate_to(client, target['x'], target['y'], target.get('yaw', 0.0), target_name)
            else:
                rospy.logwarn(f"No matching landmark for '{command}'.")
        rate.sleep()

if __name__ == '__main__':
    main()

