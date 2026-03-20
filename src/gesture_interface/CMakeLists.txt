cmake_minimum_required(VERSION 3.8)
project(gesture_interface)

# Use ament_python since this is a Python-based package
find_package(ament_python REQUIRED)
find_package(rclpy REQUIRED)
find_package(gesture_interface_msgs REQUIRED)  # Our service package

# Install Python modules
ament_python_install_package(${PROJECT_NAME})

# Install launch/config/gesture folders
install(DIRECTORY launch config gestures
        DESTINATION share/${PROJECT_NAME})

# Export dependencies
ament_export_dependencies(gesture_interface_msgs)

ament_package()
