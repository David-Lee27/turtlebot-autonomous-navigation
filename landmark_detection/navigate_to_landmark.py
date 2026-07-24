#!/usr/bin/env python3
import rospy
import yaml
import math
import speech_recognition as sr
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler

# 📂 YAML file with landmarks
LANDMARKS_FILE = "/home/david/catkin_ws/src/image_logger/scripts/landmarks.yaml"

def load_landmarks(filepath):
    with open(filepath, 'r') as f:
        return yaml.safe_load(f) or {}

def recognize_command():
    r = sr.Recognizer()
    with sr.Microphone() as source:
        rospy.loginfo("Listening for a landmark name...")
        audio = r.listen(source)
    try:
        command = r.recognize_google(audio)
        rospy.loginfo(f"Heard: '{command}'")
        return command.lower().strip()
    except sr.UnknownValueError:
        rospy.logwarn("Speech not understood")
        return None
    except sr.RequestError as e:
        rospy.logerr(f"Speech recognition failed: {e}")
        return None

def go_to_landmark(name, landmarks, pub):
    if name not in landmarks:
        rospy.logwarn(f"No landmark named '{name}'!")
        return

    coords = landmarks[name]
    x = coords.get('x', 0.0)
    y = coords.get('y', 0.0)
    yaw = coords.get('yaw', 0.0)

    q = quaternion_from_euler(0, 0, yaw)
    goal = PoseStamped()
    goal.header.frame_id = "map"
    goal.header.stamp = rospy.Time.now()
    goal.pose.position.x = x
    goal.pose.position.y = y
    goal.pose.position.z = 0.0
    goal.pose.orientation.x = q[0]
    goal.pose.orientation.y = q[1]
    goal.pose.orientation.z = q[2]
    goal.pose.orientation.w = q[3]

    rospy.loginfo(f"Publishing goal to '{name}': (x={x}, y={y}, yaw={yaw})")
    pub.publish(goal)

def main():
    rospy.init_node('voice_command_navigator')
    pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=1)
    rospy.sleep(1.0)  # wait for publisher setup

    landmarks = load_landmarks(LANDMARKS_FILE)
    rospy.loginfo(f"Loaded landmarks: {list(landmarks.keys())}")

    rate = rospy.Rate(1)
    while not rospy.is_shutdown():
        command = recognize_command()
        if command:
            # match landmark name inside command
            target = None
            for name in landmarks.keys():
                if name.lower() in command:
                    target = name
                    break
            if target:
                go_to_landmark(target, landmarks, pub)
            else:
                rospy.logwarn(f"No matching landmark for '{command}'")
        rate.sleep()

if __name__ == '__main__':
    try:
        main()
    except rospy.ROSInterruptException:
        pass

