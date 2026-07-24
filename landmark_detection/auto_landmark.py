#!/usr/bin/env python3
import rospy
import yaml
import math
import actionlib
from move_base_msgs.msg import MoveBaseAction, MoveBaseGoal
from geometry_msgs.msg import Pose, PoseStamped
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from tf.transformations import euler_from_quaternion
import os

# 🔧 Configuration
LANDMARKS_FILE = "/home/david/catkin_ws/src/image_logger/scripts/landmarks.yaml"
WAYPOINTS = [
    (1.0, 0.0, 0.0),   # x, y, yaw
    (2.0, 1.0, math.pi/2),
    (0.0, 2.0, math.pi),
    # add as many as you need
]

# 📍 Shared State
current_pose = None
current_goal_index = 0
landmarks = {}

# 🤖 MoveBase Client
move_base_client = None

def send_move_base_goal(x, y, yaw):
    global move_base_client
    goal = MoveBaseGoal()
    goal.target_pose.header.frame_id = "map"
    goal.target_pose.header.stamp = rospy.Time.now()
    goal.target_pose.pose.position.x = x
    goal.target_pose.pose.position.y = y
    q = quaternion_from_euler(0, 0, yaw)
    goal.target_pose.pose.orientation.x = q[0]
    goal.target_pose.pose.orientation.y = q[1]
    goal.target_pose.pose.orientation.z = q[2]
    goal.target_pose.pose.orientation.w = q[3]

    rospy.loginfo(f"Sending goal: ({x}, {y}, {yaw})")
    move_base_client.send_goal(goal, done_cb=move_base_done_cb)

def move_base_done_cb(status, result):
    global current_goal_index
    rospy.loginfo(f"Goal {current_goal_index} reached!")
    current_goal_index += 1
    if current_goal_index < len(WAYPOINTS):
        x, y, yaw = WAYPOINTS[current_goal_index]
        send_move_base_goal(x, y, yaw)
    else:
        rospy.loginfo("All goals completed!")
        rospy.signal_shutdown()

def odom_callback(msg):
    global current_pose
    current_pose = msg.pose.pose

def detected_landmark_callback(msg):
    global landmarks
    if current_pose is None:
        return
    landmark_name = msg.data.lower()
    rospy.loginfo(f"Detected landmark: {landmark_name}")

    pos = current_pose.position
    ori = current_pose.orientation
    roll, pitch, yaw = euler_from_quaternion([ori.x, ori.y, ori.z, ori.w])
    landmarks[landmark_name] = {'x': pos.x, 'y': pos.y, 'yaw': yaw}
    rospy.loginfo(f"Saving {landmark_name} at ({pos.x:.2f},{pos.y:.2f},{yaw:.2f})")

    # Save to file
    with open(LANDMARKS_FILE, 'w') as f:
        yaml.safe_dump(landmarks, f)

def main():
    rospy.init_node('auto_explore_and_landmark')
    rospy.Subscriber('/odom', Odometry, odom_callback)
    rospy.Subscriber('/detected_landmark_name', String, detected_landmark_callback)

    global move_base_client
    move_base_client = actionlib.SimpleActionClient('move_base', MoveBaseAction)
    rospy.loginfo("Waiting for move_base...")
    move_base_client.wait_for_server()

    # Load existing landmarks if present
    if os.path.exists(LANDMARKS_FILE):
        with open(LANDMARKS_FILE) as f:
            loaded = yaml.safe_load(f) or {}
            landmarks.update(loaded)

    # Start the first goal
    if WAYPOINTS:
        x, y, yaw = WAYPOINTS[0]
        send_move_base_goal(x, y, yaw)
    rospy.spin()

if __name__ == '__main__':
    main()

