"""
human_detection.py
==================
ROS 2 Node that provides a ``/yahboom_esp32/vision/human_detection`` service.

Service type: yahboom_interfaces/srv/HumanDetection
  Request:  float64 timeout   – seconds to wait for a valid human detection
  Response: bool    detected  – True if a human was found before timeout

How it works
------------
When the service is called, the node checks the latest cached frame from the
image_proc topic. It runs MediaPipe Pose and counts visible pose landmarks.
If LANDMARK_THRESHOLD is met within timeout, detected=True is returned.

Threading model
---------------
A MultiThreadedExecutor is REQUIRED so the image subscriber can update
self._frame while the service callback blocks in its polling loop.
The two callbacks are in the same ReentrantCallbackGroup which lets them
run concurrently on different threads.

Topics subscribed
-----------------
  /yahboom/vision/camera/image_raw  (sensor_msgs/Image)

Services offered
----------------
  /yahboom_esp32/vision/human_detection  (yahboom_interfaces/srv/HumanDetection)
"""

import threading
import time

import cv2
import mediapipe as mp
import rclpy
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from rclpy.node import Node
from cv_bridge import CvBridge
from sensor_msgs.msg import Image

from yahboom_interfaces.srv import HumanDetection


# ── Tuneable constants ──────────────────────────────────────────────────────────
# Minimum per-landmark visibility score (0.0 – 1.0) to count a landmark
VISIBILITY_THRESHOLD: float = 0.5

# Minimum number of visible landmarks to classify a detection as "human"
# MediaPipe Pose has 33 landmarks total; requiring 15+ is a robust threshold
LANDMARK_THRESHOLD: int = 15

# Default timeout used when the caller sends timeout <= 0
DEFAULT_TIMEOUT_SEC: float = 5.0

# Image topic published by image_proc.py
IMAGE_TOPIC: str = '/yahboom/vision/camera/image_raw'

# Service name
SERVICE_NAME: str = '/yahboom_esp32/vision/human_detection'
# ───────────────────────────────────────────────────────────────────────────────


class HumanDetectionNode(Node):
    def __init__(self):
        super().__init__('human_detection_node')

        self._bridge = CvBridge()
        self._cb_group = ReentrantCallbackGroup()

        # MediaPipe Pose – static_image_mode=False for video stream performance
        self._mp_pose = mp.solutions.pose.Pose(
            static_image_mode=False,
            model_complexity=0,          # 0 = fastest (Lite), 1 = Full, 2 = Heavy
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
        )

        # Latest frame and a lock to protect it across threads
        self._frame = None
        self._frame_lock = threading.Lock()

        # BUG-03 FIX: detection_event lets the service callback wake up
        # immediately when the image subscriber processes a new frame,
        # avoiding a tight 50 ms sleep loop.
        self._detection_event = threading.Event()

        # Image subscriber (always running so frames are warm when service fires)
        self._image_sub = self.create_subscription(
            Image,
            IMAGE_TOPIC,
            self._image_callback,
            5,
            callback_group=self._cb_group,
        )

        # Service server
        self._srv = self.create_service(
            HumanDetection,
            SERVICE_NAME,
            self._detect_callback,
            callback_group=self._cb_group,
        )

        self.get_logger().info(
            f'HumanDetectionNode ready – service: {SERVICE_NAME}')
        self.get_logger().info(
            f'Thresholds: visibility>={VISIBILITY_THRESHOLD}, '
            f'landmarks>={LANDMARK_THRESHOLD}')

    # ── Subscriber ──────────────────────────────────────────────────────────────

    def _image_callback(self, msg: Image):
        """Cache the latest frame and signal the service callback."""
        try:
            frame = self._bridge.imgmsg_to_cv2(msg, desired_encoding='bgr8')
            with self._frame_lock:
                self._frame = frame
            # BUG-03 FIX: notify service callback that a fresh frame is ready
            self._detection_event.set()
        except Exception as exc:
            self.get_logger().warn(f'cv_bridge error: {exc}')

    # ── Detection helper ────────────────────────────────────────────────────────

    def _is_human_in_frame(self, frame) -> bool:
        """
        Run MediaPipe Pose on *frame* and return True if the number of
        visible landmarks meets LANDMARK_THRESHOLD.
        """
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self._mp_pose.process(rgb)

        if not results.pose_landmarks:
            return False

        visible_count = sum(
            1 for lm in results.pose_landmarks.landmark
            if lm.visibility >= VISIBILITY_THRESHOLD
        )
        self.get_logger().debug(f'Visible landmarks: {visible_count}/{LANDMARK_THRESHOLD}')
        return visible_count >= LANDMARK_THRESHOLD

    # ── Service callback ────────────────────────────────────────────────────────

    def _detect_callback(self, request: HumanDetection.Request,
                         response: HumanDetection.Response):
        """
        Wait up to *timeout* seconds for a human to be detected.

        Uses threading.Event instead of a fixed sleep loop:
        - The service callback blocks on _detection_event.wait()
        - Each time the image subscriber delivers a new frame it calls
          _detection_event.set(), waking this callback immediately.
        - This is safe because MultiThreadedExecutor runs both callbacks
          on separate threads.
        """
        timeout = float(request.timeout) if request.timeout > 0 else DEFAULT_TIMEOUT_SEC
        deadline = time.monotonic() + timeout

        self.get_logger().info(
            f'HumanDetection requested – timeout: {timeout:.1f} s')

        detected = False
        while time.monotonic() < deadline:
            remaining = deadline - time.monotonic()

            # BUG-03 FIX: block until a new frame arrives (or timeout expires)
            # This avoids spinning at 20 Hz when no frames are incoming.
            self._detection_event.clear()
            got_frame = self._detection_event.wait(timeout=min(remaining, 1.0))

            if not got_frame:
                self.get_logger().warn(
                    'No frame received – is image_proc running?',
                    throttle_duration_sec=2.0)
                continue

            with self._frame_lock:
                frame = self._frame.copy() if self._frame is not None else None

            if frame is not None and self._is_human_in_frame(frame):
                detected = True
                break

        response.detected = detected
        self.get_logger().info(
            f'HumanDetection result: detected={detected}')
        return response

    # ── BUG-11 FIX: clean up MediaPipe resources on shutdown ────────────────────

    def destroy_node(self):
        """Release MediaPipe Pose resources before the node is destroyed."""
        try:
            self._mp_pose.close()
            self.get_logger().info('MediaPipe Pose closed.')
        except Exception:
            pass
        super().destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = HumanDetectionNode()

    # MultiThreadedExecutor is REQUIRED:
    # the image subscriber must keep updating self._frame while the
    # service callback is blocked waiting on _detection_event.
    executor = MultiThreadedExecutor()
    executor.add_node(node)

    try:
        executor.spin()
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
