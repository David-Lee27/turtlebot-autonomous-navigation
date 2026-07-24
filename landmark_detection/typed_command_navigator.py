#!/usr/bin/env python3

import rospy
import actionlib
import yaml
import os
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Quaternion
from tf.transformations import quaternion_from_euler

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
    rospy.loginfo(f"Navigating to x={x:.2f}, y={y:.2f}, yaw={yaw:.2f}")
    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "map"
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    goal.target_pose.pose.position.z = 0.0

    # Convert yaw (in radians) to quaternion (simplified for yaw only)
    import tf
    quat = tf.transformations.quaternion_from_euler(0, 0, yaw)
    goal.target_pose.pose.orientation.x = quat[0]
    goal.target_pose.pose.orientation.y = quat[1]
    goal.target_pose.pose.orientation.z = quat[2]
    goal.target_pose.pose.orientation.w = quat[3]

    client.send_goal(goal)
    client.wait_for_result()

def main():
    rospy.init_node('typed_command_navigator')
    client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    rospy.loginfo("Waiting for move_base action server...")
    client.wait_for_server()
    rospy.loginfo("Connected to move_base.")

    current_floor = ""
    landmarks = {}

    while not rospy.is_shutdown():
        cmd = input("\nType a command (e.g. 'robot go to kitchen'): ").strip().lower()

        if "robot" not in cmd:
            print("Missing keyword 'robot'; ignoring.")
            continue

        # Handle floor switch
        if "upstairs" in cmd:
            current_floor = "upstairs"
            landmarks = load_landmarks(UPSTAIRS_LANDMARKS)
            rospy.loginfo("Switched to upstairs landmarks.")
            continue
        elif "downstairs" in cmd:
            current_floor = "downstairs"
            landmarks = load_landmarks(DOWNSTAIRS_LANDMARKS)
            rospy.loginfo("Switched to downstairs landmarks.")
            continue

        if not landmarks:
            print("No floor selected yet. Type 'robot go upstairs' or 'robot go downstairs' first.")
            continue

        # Search for known landmark
        matched = None
        for name in landmarks.keys():
            if name.lower() in cmd:
                matched = name
                break

        if matched:
            goal = landmarks[matched]
            rospy.loginfo(f"Navigating to '{matched}' on {current_floor}...")
            print("typepppppppppppppppppp",type(goal['x']))
            navigate_to(client, goal['x'], goal['y'], goal.get('yaw', 0.0))
            #navigate_to(client, x=-1.4817084074020386, y=-1.108750581741333, yaw=1.57)
            rospy.loginfo(f"Arrived at '{matched}'")
        else:
            print("No matching landmark found in command.")

if __name__ == '__main__':
    main()