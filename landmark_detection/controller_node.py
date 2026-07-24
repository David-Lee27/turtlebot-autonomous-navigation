#!/usr/bin/env python3
import rospy
import yaml
import os
from nav_msgs.msg import Odometry
from std_msgs.msg import String
from tf.transformations import euler_from_quaternion

landmarks = {}
current_pose = None
landmarks_file = ""

def odom_callback(msg):
    global current_pose
    current_pose = msg.pose.pose

def detected_landmark_callback(msg):
    global landmarks, current_pose, landmarks_file
    if current_pose is None:
        rospy.logwarn("Current pose not yet received, cannot save landmark.")
        return

    landmark_name = msg.data.lower().strip()
    rospy.loginfo(f"Detected landmark: {landmark_name}")

    # Skip if already saved
    if landmark_name in landmarks:
        rospy.loginfo(f"Landmark '{landmark_name}' already saved, skipping")
        return

    # Get current robot pose
    pos = current_pose.position
    ori = current_pose.orientation
    roll, pitch, yaw = euler_from_quaternion([ori.x, ori.y, ori.z, ori.w])

    landmarks[landmark_name] = {'x': pos.x, 'y': pos.y, 'yaw': yaw}
    rospy.loginfo(f"Saving {landmark_name} at (x={pos.x:.2f}, y={pos.y:.2f}, yaw={yaw:.2f})")

    # Ensure directory exists
    os.makedirs(os.path.dirname(landmarks_file), exist_ok=True)

    # Save landmarks to YAML file
    try:
        with open(landmarks_file, 'w') as f:
            yaml.safe_dump(landmarks, f, sort_keys=False)
    except Exception as e:
        rospy.logerr(f"Failed to write landmarks to {landmarks_file}: {e}")

def main():
    global landmarks_file, landmarks, current_pose

    rospy.init_node('controller_node')

    # Get floor parameter (default to downstairs)
    floor = rospy.get_param('~floor', 'downstairs').lower()

    # Set landmarks file path based on floor
    base_dir = '/home/david/habitat_ws/src/image_logger/scripts'
    if floor == 'upstairs':
        landmarks_file_path = os.path.join(base_dir, 'upstairs_landmarks.yaml')
    else:
        landmarks_file_path = os.path.join(base_dir, 'downstairs_landmarks.yaml')

    landmarks_file = rospy.get_param('~landmarks_file', landmarks_file_path)
    rospy.loginfo(f"Using landmarks file: {landmarks_file} for floor '{floor}'")

    landmarks = {}
    current_pose = None

    # Load existing landmarks if available
    if os.path.exists(landmarks_file):
        try:
            with open(landmarks_file, 'r') as f:
                landmarks = yaml.safe_load(f) or {}
            rospy.loginfo(f"Loaded {len(landmarks)} landmarks from {landmarks_file}")
        except Exception as e:
            rospy.logwarn(f"Failed to load landmarks from {landmarks_file}: {e}")

    rospy.Subscriber('/odom', Odometry, odom_callback)
    rospy.Subscriber('/detected_landmark_name', String, detected_landmark_callback)

    rospy.loginfo("Controller node is logging landmarks dynamically...")
    rospy.spin()

if __name__ == '__main__':
    main()

