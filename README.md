# Work in progress: VantTec's Unmanned Underwater Vehicle (UUV) Repository.

**How to start working?**


```Shell
cd
git clone --recurse-submodules https://github.com/vanttec/vanttec_uuv.git

cd vanttec_uuv && git checkout feature/integration

chmod +x create_container_gpu.bash
docker build -t uuv .
./create_container_gpu.bash
docker exec -it uuv /bin/bash

# Inside the container
cd /ws/vanttec_uuv/
catkin_make
source ~/.bashrc


- **arduino_br**: ROS package that uses rosserial_python and rosserial_arduino to interface with the T-100 and the T-200 thrusters.
- **vectornav_ros**: ROS package that allows the USV to interface with Vectornav's IMUs.
- **zed_ros_wrapper**: ROS package for the Stereolabs ZED Camera.