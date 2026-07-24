#!/usr/bin/env python3
import rospy
import yaml
import os
from std_msgs.msg import String
from geometry_msgs.msg import PoseStamped

class LandmarkNavigator:
    def __init__(self):
        rospy.init_node('landmark_navigator')

        # Load landmarks from YAML file
        yaml_path = rospy.get_param('~landmark_yaml_path', 'landmarks.yaml')
        if not os.path.isabs(yaml_path):
            # Assume relative to package path
            pkg_path = rospy.get_param('~package_path', '/home/user/catkin_ws/src/image_logger')
            yaml_path = os.path.join(pkg_path, yaml_path)

        rospy.loginfo(f"Loading landmarks from: {yaml_path}")
        with open(yaml_path, 'r') as f:
            self.landmarks = yaml.safe_load(f)

        self.pub = rospy.Publisher('/move_base_simple/goal', PoseStamped, queue_size=1)
        rospy.Subscriber('/voice_commands', String, self.voice_callback)

        rospy.loginfo("Landmark Navigator Node Ready")
        rospy.spin()

    def voice_callback(self, msg):
        command = msg.data.lower().strip()
        rospy.loginfo(f"Received voice command: '{command}'")

        if command in self.landmarks:
            coords = self.landmarks[command]
            rospy.loginfo(f"Navigating to landmark '{command}' at {coords}")

            goal = PoseStamped()
            goal.header.frame_id = "map"
            goal.header.stamp = rospy.Time.now()

            goal.pose.position.x = coords['x']
            goal.pose.position.y = coords['y']
            goal.pose.position.z = 0.0

            # Assuming no rotation needed, face forward:
            goal.pose.orientation.x = 0.0
            goal.pose.orientation.y = 0.0
            goal.pose.orientation.z = 0.0
            goal.pose.orientation.w = 1.0

            self.pub.publish(goal)
            rospy.loginfo(f"Goal sent to move_base_simple/goal")
        else:
            rospy.logwarn(f"Landmark '{command}' not found in YAML")

if __name__ == '__main__':
    try:
        LandmarkNavigator()
    except rospy.ROSInterruptException:
        pass

