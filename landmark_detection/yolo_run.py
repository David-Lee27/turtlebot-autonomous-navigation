#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
import torch
import cv2
import tf
from landmark_saver import LandmarkSaver
import warnings
warnings.filterwarnings("ignore", category=FutureWarning)


class YoloObjectDetector:
    def __init__(self):
        rospy.init_node('yolo_object_detector')
        self.image_topic = rospy.get_param('~image_topic', '/zed2/zed_node/rgb/image_rect_color')
        self.bridge = CvBridge()
        self.tf_listener = tf.TransformListener()
        self.landmark_saver = LandmarkSaver("/tmp/landmarks.yaml")

        rospy.loginfo("Loading YOLOv5 model...")
        # Load model on CPU (change 'cpu' to 'cuda' if GPU available and configured)
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, device='cpu')
        self.model.eval()
        rospy.loginfo("YOLOv5 model loaded successfully!")

        rospy.sleep(1.0)  # Allow TF buffer to fill

        rospy.Subscriber(self.image_topic, Image, self.image_callback)
        rospy.loginfo(f"Subscribed to image topic: {self.image_topic}")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            rospy.logwarn(f"Failed to convert ROS Image to OpenCV image: {e}")
            return

        # Convert BGR to RGB for model input
        cv_image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        # Perform detection
        results = self.model(cv_image_rgb)
        detections = results.pandas().xyxy[0]

        detected_objects = []
        for _, row in detections.iterrows():
            label = row['name']
            confidence = row['confidence']
            if confidence > 0.9:
                detected_objects.append(label)

        if not detected_objects:
            rospy.loginfo("No objects detected above confidence threshold.")
            return

        rospy.loginfo(f"Detected objects: {detected_objects}")

        # Try to get robot pose in 'map' frame
        try:
            (trans, rot) = self.tf_listener.lookupTransform('map', 'base_link', rospy.Time(0))
            _, _, yaw = tf.transformations.euler_from_quaternion(rot)

            for obj_name in detected_objects:
                self.landmark_saver.save_landmark(obj_name, trans[0], trans[1], yaw)
                rospy.loginfo(f"Saved landmark '{obj_name}' at x={trans[0]:.2f}, y={trans[1]:.2f}, yaw={yaw:.2f}")

        except (tf.LookupException, tf.ConnectivityException, tf.ExtrapolationException) as e:
            rospy.logwarn(f"TF lookup failed: {e}")

if __name__ == '__main__':
    try:
        detector = YoloObjectDetector()
        rospy.spin()
    except rospy.ROSInterruptException:
        pass

