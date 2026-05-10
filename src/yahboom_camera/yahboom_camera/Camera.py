import time
import cv2

import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CompressedImage

IMSHOW = False

class ABU_CAMERA(Node):
    def __init__(self, name):

        super().__init__(name)
        self.get_logger().info("Node is initializing....")
        
        self.frame = None

        self.bridge = CvBridge()

        self.raw_image_pub_ = self.create_publisher(Image, '/yahboom/vision/camera/image_raw', 1)
        self.debug_image_pub_ = self.create_publisher(Image, '/yahboom/vision/camera/image_raw', 1)
        self.image_sub_ = self.create_subscription(CompressedImage, '/espRos/esp32camera', self.handleTopic, 1)

        self.timer = self.create_timer(1/30, lambda: self.image_publisher(mode="raw_image"))

        self.get_logger().info("Node finish initialize.")

    def image_publisher(self, mode, frame=None):

        if self.frame is not None:            
            # self.get_logger().info(f"Publish image in mode: {mode}")

            if mode == "raw_image":
                data = self.bridge.cv2_to_imgmsg(self.frame, encoding="bgr8")
                self.raw_image_pub_.publish(data)
            elif mode == "debug_image":
                data = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
                self.debug_image_pub_.publish(data)
            else:
                self.get_logger().error("Mode must be [raw_image, debug_image]")
                raise Exception("Mode must be [raw_image, debug_image]")

    def handleTopic(self, msg):
        frame = self.bridge.compressed_imgmsg_to_cv2(msg)
        frame = cv2.resize(frame, (1920, 1080))

        if IMSHOW:
            cv2.imshow('frame', frame)
            cv2.waitKey(1)

        self.frame = frame

    def image_processing(self, frame):
        text = "Hello, YAHBOOM ABU!"
        position = (100, 250)     
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 2
        color = (0, 255, 0)       
        thickness = 3
        line_type = cv2.LINE_AA    
        cv2.putText(frame, text, position, font, font_scale, color, thickness, line_type)

        return frame

def main():
    rclpy.init()
    esp_img = ABU_CAMERA("abu_camera") 
    try:
        rclpy.spin(esp_img)
    except KeyboardInterrupt:
        pass
    finally:
        esp_img.destroy_node()
        rclpy.shutdown()
