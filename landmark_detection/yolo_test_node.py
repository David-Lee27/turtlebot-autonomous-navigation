#!/usr/bin/env python3
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import torch
import cv2
import tf

class YoloTestNode:
    def __init__(self):
        rospy.init_node('yolo_test_node')
        self.image_topic = rospy.get_param('~image_topic', '/zed2/zed_node/rgb/image_rect_color')
        self.bridge = CvBridge()
        self.tf_listener = tf.TransformListener()

        rospy.loginfo("Loading YOLOv5 model...")
        self.model = torch.hub.load('ultralytics/yolov5', 'yolov5s', pretrained=True, device='cpu')
        rospy.loginfo("Model loaded successfully!")

        rospy.sleep(1.0)  # Allow TF buffer to fill

        rospy.Subscriber(self.image_topic, Image, self.image_callback)

    def image_callback(self, msg):
        rospy.loginfo("Received image")
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except Exception as e:
            rospy.logwarn(f"Failed to convert image: {e}")
            return

        # Just do a quick TF lookup test
        try:
            (trans, rot) = self.tf_listener.lookupTransform('map', 'base_link', rospy.Time(0))
            rospy.loginfo(f"TF lookup success: trans={trans}, rot={rot}")
        except Exception as e:
            rospy.logwarn(f"TF lookup failed: {e}")
            return

        # Convert to RGB
        cv_image_rgb = cv2.cvtColor(cv_image, cv2.COLOR_BGR2RGB)

        # Run YOLO inference and time it
        import time
        start = time.time()
        results = self.model(cv_image_rgb)
        duration = time.time() - start
        rospy.loginfo(f"Inference took {duration:.3f} seconds")

        # Print detected object names (with confidence > 0.5)
        detections = results.pandas().xyxy[0]
        detected_objects = []
        for _, row in detections.iterrows():
            if row['confidence'] > 0.5:
                detected_objects.append(row['name'])
        rospy.loginfo(f"Detected objects: {detected_objects}")

if __name__ == '__main__':
    node = YoloTestNode()
    rospy.spin()

