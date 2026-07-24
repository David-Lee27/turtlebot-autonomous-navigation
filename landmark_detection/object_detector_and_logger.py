#!/usr/bin/env python3
import rospy
from std_msgs.msg import String
from sensor_msgs.msg import Image
from cv_bridge import CvBridge, CvBridgeError
from ultralytics import YOLO
import cv2  # Import OpenCV for drawing

class ObjectDetectorAndLogger:
    def __init__(self):
        rospy.init_node('object_detector')
        self.image_topic = rospy.get_param(
            '~image_topic',
            '/zed2/zed_node/rgb/image_rect_color'
        )
        rospy.loginfo(f"Object Detector subscribing to image topic: {self.image_topic}")

        # Publisher for detected landmarks
        self.landmark_pub = rospy.Publisher(
            '/detected_landmark_name',
            String,
            queue_size=10
        )

        # Publisher for the image with detected bounding boxes
        self.annotated_image_pub = rospy.Publisher(
            '/detected_image',
            Image,
            queue_size=10
        )

        self.bridge = CvBridge()

        # Load the YOLO model
        rospy.loginfo("Loading YOLOv5s model...")
        self.model = YOLO('yolov5s.pt')
        rospy.loginfo("YOLOv5s model loaded successfully!")

        # Subscribe to image topic
        rospy.Subscriber(self.image_topic, Image, self.image_callback)
        rospy.loginfo("Object Detector node started.")

    def image_callback(self, msg):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
        except CvBridgeError as e:
            rospy.logerr(f"CV Bridge error: {e}")
            return

        # Run detection
        results = self.model(cv_image)

        # Get the annotated image from the results
        # results.render() modifies the image in-place if called with a list of results
        # or returns a list of annotated images.
        # For a single image input, results[0].plot() is a convenient way to get the annotated image.
        annotated_image = results[0].plot() # This returns a numpy array (cv2 image) with detections drawn

        # Iterate over detected objects and publish their class names
        for box in results[0].boxes:
            confidence = float(box.conf[0])
            if confidence >= 0.9:
                class_id = int(box.cls[0])
                detected_name = results[0].names[class_id].lower().strip()
                rospy.loginfo(f"Detected landmark in image: {detected_name}")

                self.landmark_pub.publish(String(detected_name))

        # Publish the annotated image
        try:
            annotated_img_msg = self.bridge.cv2_to_imgmsg(annotated_image, encoding='bgr8')
            annotated_img_msg.header = msg.header # Maintain the original timestamp and frame_id
            self.annotated_image_pub.publish(annotated_img_msg)
        except CvBridgeError as e:
            rospy.logerr(f"CV Bridge error when publishing annotated image: {e}")

    def spin(self):
        rospy.spin()

if __name__ == '__main__':
    node = ObjectDetectorAndLogger()
    node.spin()