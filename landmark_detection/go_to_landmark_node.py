#!/usr/bin/env python3
import rospy
import yaml
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped
from tf.transformations import quaternion_from_euler

# Load landmarks
LANDMARKS_FILE = '/path/to/landmarks.yaml'
with open(LANDMARKS_FILE) as f:
    landmarks = yaml.safe_load(f)

current_floor = "downstairs"
pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=10)

def set_floor(msg):
    global current_floor
    current_floor = msg.data.lower().strip()
    rospy.loginfo(f"Switched to floor: {current_floor}")

def handle_command(msg):
    target = msg.data.lower().strip().replace(' ', '_')
    floor_landmarks = landmarks.get(current_floor, {})
    if target in floor_landmarks:
        coords = floor_landmarks[target]
        q = quaternion_from_euler(0, 0, coords['yaw'])
        goal = PoseStamped()
        goal.header.frame_id = "map"
        goal.header.stamp = rospy.Time.now()
        goal.pose.position.x = coords['x']
        goal.pose.position.y = coords['y']
        goal.pose.orientation.x, goal.pose.orientation.y, goal.pose.orientation.z, goal.pose.orientation.w = q
        rospy.loginfo(f"Moving to {target} on {current_floor}")
        pub.publish(goal)
    else:
        rospy.logwarn(f"Unknown landmark: {target} on {current_floor}")

rospy.init_node('go_to_landmark_node')
rospy.Subscriber('/voice_commands', String, handle_command)
rospy.Subscriber('/floor_command', String, set_floor)
rospy.spin()

