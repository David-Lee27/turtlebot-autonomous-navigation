#!/usr/bin/env python3
import rospy
import subprocess
from std_msgs.msg import String

class MapSwitcher:
    def __init__(self):
        rospy.init_node('voice_map_switcher')

        # Paths to your maps
        self.maps = {
            'downstairs': '/home/david/catkin_ws/src/image_logger/maps/downstairs.yaml',
            'upstairs': '/home/david/catkin_ws/src/image_logger/maps/upstairs.yaml'
        }

        # Store subprocess handles for map_server and amcl so we can kill them
        self.map_server_proc = None
        self.amcl_proc = None

        # Subscribe to your voice command topic
        rospy.Subscriber('/voice_commands', String, self.voice_callback)

        rospy.loginfo("Voice Map Switcher ready, say 'upstairs' or 'downstairs'")

    def voice_callback(self, msg):
        command = msg.data.lower().strip()
        rospy.loginfo(f"Voice command received: {command}")

        if command in self.maps:
            self.switch_map(command)
        else:
            rospy.logwarn(f"Unknown command '{command}'")

    def kill_process(self, proc):
        if proc and proc.poll() is None:
            rospy.loginfo("Killing existing process")
            proc.terminate()
            proc.wait()

    def switch_map(self, floor):
        rospy.loginfo(f"Switching to {floor} map")

        # Kill old processes
        self.kill_process(self.map_server_proc)
        self.kill_process(self.amcl_proc)

        map_path = self.maps[floor]

        # Launch map_server with the map yaml
        self.map_server_proc = subprocess.Popen([
            'roslaunch', 'map_server', 'map_server.launch',
            f'map:={map_path}'
        ])

        rospy.sleep(2)  # wait a bit for map_server to initialize

        # Launch AMCL with the map yaml
        self.amcl_proc = subprocess.Popen([
            'roslaunch', 'turtlebot3_navigation', 'amcl.launch',
            f'map_file:={map_path}'
        ])

if __name__ == '__main__':
    try:
        switcher = MapSwitcher()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

