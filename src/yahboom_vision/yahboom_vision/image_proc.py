import time
import cv2

import rclpy
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CompressedImage

# Set to True to preview the raw image in a local OpenCV window (requires display).
# Prefer using rqt_image_view in production instead of enabling this.
IMSHOW = False


class YAHBOOM_VISION(Node):
    def __init__(self, name):
        super().__init__(name)
        self.get_logger().info("Node is initializing....")

        self.frame = None
        # BUG-07 FIX: dirty flag — only publish when a NEW frame has arrived
        self._frame_updated = False

        self.bridge = CvBridge()

        self.raw_image_pub_   = self.create_publisher(Image, '/yahboom/vision/camera/image_raw', 1)
        self.debug_image_pub_ = self.create_publisher(Image, '/yahboom/vision/camera/debug', 1)
        self.image_sub_       = self.create_subscription(
            CompressedImage, '/espRos/esp32camera', self.handleTopic, 1)

        # Publish at 30 Hz — but only when a new frame is available (dirty flag)
        self.timer  = self.create_timer(1 / 30, lambda: self.image_publisher(mode="raw_image"))
        self.timer1 = self.create_timer(1 / 30, self.image_processing)

        self.get_logger().info("Node finish initialize.")

    # ── Subscriber ──────────────────────────────────────────────────────────────

    def handleTopic(self, msg):
        frame = self.bridge.compressed_imgmsg_to_cv2(msg)

        # BUG-02 FIX: removed cv2.resize(frame, (1920, 1080)).
        # ESP32-CAM native resolution is ~640×480; upscaling wastes CPU and
        # does not add information. MediaPipe receives the frame as-is which
        # is faster and produces the same detection quality.

        if IMSHOW:
            cv2.imshow('frame', frame)
            cv2.waitKey(1)

        self.frame = frame
        self._frame_updated = True  # mark that a new frame is ready

    # ── Publishers ──────────────────────────────────────────────────────────────

    def image_publisher(self, mode, frame=None):
        # BUG-07 FIX: skip publish if no new frame has arrived since last publish
        if self.frame is None:
            return
        if mode == "raw_image" and not self._frame_updated:
            return

        if mode == "raw_image":
            data = self.bridge.cv2_to_imgmsg(self.frame, encoding="bgr8")
            self.raw_image_pub_.publish(data)
            self._frame_updated = False   # consumed — reset dirty flag
        elif mode == "debug_image":
            if frame is None:
                return
            data = self.bridge.cv2_to_imgmsg(frame, encoding="bgr8")
            self.debug_image_pub_.publish(data)
        else:
            self.get_logger().error("Mode must be [raw_image, debug_image]")
            raise ValueError("Mode must be [raw_image, debug_image]")

    # ── Processing ──────────────────────────────────────────────────────────────

    def image_processing(self):
        if self.frame is None:
            return

        _frame = self.frame.copy()
        text       = "Hello, YAHBOOM!"
        position   = (100, 250)
        font       = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 2
        color      = (0, 255, 0)
        thickness  = 3
        line_type  = cv2.LINE_AA
        cv2.putText(_frame, text, position, font, font_scale, color, thickness, line_type)

        self.image_publisher("debug_image", _frame)
        return _frame


def main():
    rclpy.init()
    esp_img = YAHBOOM_VISION("yahboom_vision")
    try:
        rclpy.spin(esp_img)
    except KeyboardInterrupt:
        pass
    finally:
        esp_img.destroy_node()
        rclpy.shutdown()
