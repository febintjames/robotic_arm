# gesture_manager_node.py

import rclpy
from rclpy.node import Node

from gesture_interface.gesture_recorder import GestureRecorder
from gesture_interface.gesture_player import GesturePlayer
from gesture_interface.gesture_storage import GestureStorage

from gesture_interface_msgs.srv import StartRecording, StopSaveRecording, PlayGesture


class GestureManager(Node):

    def __init__(self):
        super().__init__("gesture_manager")

        self.get_logger().info("Gesture Manager started")

        # Initialize subsystems
        self.storage = GestureStorage(self)
        self.recorder = GestureRecorder(self)
        self.player = GesturePlayer(self)

        self.recording_active = False

        # Services
        self.create_service(StartRecording, "/start_recording", self.start_recording_callback)
        self.create_service(StopSaveRecording, "/stop_save_recording", self.stop_save_callback)
        self.create_service(PlayGesture, "/play_gesture", self.play_callback)

    # -----------------------------
    # Start Recording Service
    # -----------------------------
    def start_recording_callback(self, request, response):
        if self.recording_active:
            response.success = False
            response.message = "Recording already in progress"
            return response

        if not self.recorder.start():
            response.success = False
            response.message = "Failed to start recording (no joint states)"
            return response

        self.get_logger().info("Starting gesture recording...")
        self.recording_active = True
        response.success = True
        response.message = "Recording started"
        return response

    # -----------------------------
    # Stop Recording and Save Gesture
    # -----------------------------
    def stop_save_callback(self, request, response):
        if not self.recording_active:
            response.success = False
            response.message = "No active recording"
            return response

        self.get_logger().info(f"Stopping recording and saving gesture as '{request.name}'")
        self.recording_active = False

        trajectory = self.recorder.stop()
        if trajectory is None or not trajectory.points:
            response.success = False
            response.message = "Recording failed or trajectory empty"
            return response

        self.storage.save(request.name, trajectory)
        response.success = True
        response.message = f"Gesture '{request.name}' saved successfully"
        return response

    # -----------------------------
    # Play Gesture Service
    # -----------------------------
    def play_callback(self, request, response):
        self.get_logger().info(f"Playing gesture '{request.name}'")

        trajectory = self.storage.load(request.name)
        if trajectory is None:
            response.success = False
            response.message = "Gesture not found"
            return response

        success = self.player.play(trajectory)
        response.success = success
        response.message = "Playback completed" if success else "Playback failed"
        return response


def main(args=None):
    rclpy.init(args=args)
    node = GestureManager()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
