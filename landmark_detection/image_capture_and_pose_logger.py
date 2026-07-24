#!/usr/bin/env python3
import rospy
import cv2
import os
import csv
import tf2_ros
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from geometry_msgs.msg import PoseStamped

class ImageCaptureAndLogger:
    MAX_FOLDER_SIZE_BYTES = 5 * 1024 * 1024 * 1024  # 5 GB

    def __init__(self, save_dir, capture_interval):
        self.bridge = CvBridge()
        self.save_dir = save_dir
        self.capture_interval = capture_interval
        self.last_save_time = rospy.Time.now()

        # Prepare save directory
        os.makedirs(self.save_dir, exist_ok=True)

        # Prepare CSV file
        self.csv_path = os.path.join(self.save_dir, "image_poses.csv")
        file_exists = os.path.isfile(self.csv_path)
        self.csv_file = open(self.csv_path, 'a', newline='')
        self.csv_writer = csv.writer(self.csv_file)
        if not file_exists:
            self.csv_writer.writerow(["filename", "x", "y", "z", "qx", "qy", "qz", "qw"])

        # Setup TF buffer and listener
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer)

        # Subscribe to camera topic
        rospy.Subscriber('/zed2/zed_node/rgb/image_rect_color', Image, self.image_callback)

    def get_folder_size(self, folder):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                if os.path.isfile(fp):
                    total_size += os.path.getsize(fp)
        return total_size

    def cleanup_old_images(self):
        """Delete oldest images and their CSV entries until folder size <= MAX_FOLDER_SIZE_BYTES"""
        folder_size = self.get_folder_size(self.save_dir)
        if folder_size <= self.MAX_FOLDER_SIZE_BYTES:
            return  # no cleanup needed

        rospy.loginfo(f"Folder size {folder_size/(1024*1024):.2f} MB exceeds limit, cleaning up oldest images.")

        # Get list of image files sorted by creation time (oldest first)
        images = [f for f in os.listdir(self.save_dir) if f.endswith('.jpg')]
        images.sort(key=lambda x: os.path.getctime(os.path.join(self.save_dir, x)))

        while folder_size > self.MAX_FOLDER_SIZE_BYTES and images:
            oldest = images.pop(0)
            image_path = os.path.join(self.save_dir, oldest)
            try:
                os.remove(image_path)
                rospy.loginfo(f"Deleted old image: {oldest}")
            except Exception as e:
                rospy.logwarn(f"Failed to delete image {oldest}: {e}")
                continue

            # Remove the corresponding line from CSV
            try:
                with open(self.csv_path, 'r') as f:
                    lines = f.readlines()
                with open(self.csv_path, 'w') as f:
                    for line in lines:
                        if not line.startswith(oldest):
                            f.write(line)
            except Exception as e:
                rospy.logwarn(f"Failed to update CSV after deleting {oldest}: {e}")

            folder_size = self.get_folder_size(self.save_dir)

    def image_callback(self, msg):
        now = rospy.Time.now()
        if (now - self.last_save_time).to_sec() < self.capture_interval:
            return

        pose_stamped = self.get_robot_pose()
        if pose_stamped is None:
            rospy.logwarn("Could not get robot pose, skipping image save")
            return

        self.last_save_time = now

        # Convert ROS Image to OpenCV image
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            rospy.logwarn(f"Failed to convert image: {e}")
            return

        # Save image
        filename = f"{now.to_nsec()}.jpg"
        filepath = os.path.join(self.save_dir, filename)
        cv2.imwrite(filepath, cv_image)

        # Log pose with image filename
        self.csv_writer.writerow([
            filename,
            pose_stamped.pose.position.x, pose_stamped.pose.position.y, pose_stamped.pose.position.z,
            pose_stamped.pose.orientation.x, pose_stamped.pose.orientation.y,
            pose_stamped.pose.orientation.z, pose_stamped.pose.orientation.w
        ])
        self.csv_file.flush()

        rospy.loginfo(f"Saved image {filename} with pose ({pose_stamped.pose.position.x:.2f}, {pose_stamped.pose.position.y:.2f})")

        # Cleanup old images if folder size exceeded
        self.cleanup_old_images()

    def get_robot_pose(self):
        try:
            trans = self.tf_buffer.lookup_transform('map', 'base_link', rospy.Time(0), rospy.Duration(1.0))

            ps = PoseStamped()
            ps.header = trans.header  # copy header info (frame_id, stamp)

            # Assign translation to pose.position
            ps.pose.position.x = trans.transform.translation.x
            ps.pose.position.y = trans.transform.translation.y
            ps.pose.position.z = trans.transform.translation.z

            # Assign rotation to pose.orientation
            ps.pose.orientation.x = trans.transform.rotation.x
            ps.pose.orientation.y = trans.transform.rotation.y
            ps.pose.orientation.z = trans.transform.rotation.z
            ps.pose.orientation.w = trans.transform.rotation.w

            return ps

        except (tf2_ros.LookupException, tf2_ros.ExtrapolationException, tf2_ros.ConnectivityException) as e:
            rospy.logwarn(f"TF lookup failed: {e}")
            return None

def main():
    rospy.init_node('image_capture_and_pose_logger')
    save_dir = rospy.get_param('~save_dir', '/tmp/captured_images')
    capture_interval = rospy.get_param('~interval', 5.0)
    logger = ImageCaptureAndLogger(save_dir, capture_interval)
    rospy.spin()

if __name__ == '__main__':
    main()

