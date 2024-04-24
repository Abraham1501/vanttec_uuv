/** ----------------------------------------------------------------------------
 * @file: gazebo_interface_uuv.cpp
 * @date: September 6, 2022
 * @author: Sebastian Mtz
 * @email: sebas.martp@gmail.com
 * 
 * @brief: Publishes UUV pose to gazebo set_model_state topic.
 * -----------------------------------------------------------------------------
 **/

#include "ros/ros.h"
#include "math.h"
#include "gazebo_msgs/ModelState.h"
#include "gazebo_msgs/ModelStates.h"
#include "vanttec_msgs/EtaPose.h"
#include <geometry_msgs/Pose.h>
#include <tf2/LinearMath/Quaternion.h>
#include <tf2_geometry_msgs/tf2_geometry_msgs.h>
 
class SetState{
private:
    ros::NodeHandle nh;
    ros::Publisher pub_state = nh.advertise<gazebo_msgs::ModelState>("/gazebo/set_model_state", 1000);
    ros::Subscriber sub_state = nh.subscribe("/uuv_simulation/dynamic_model/eta_pose", 1000, &SetState::stateCallback, this);
    ros::Subscriber sub_gaz_state = nh.subscribe("/gazebo/model_states", 1000, &SetState::gazStateCallback, this);
    tf2::Quaternion q;
    tf2::Quaternion q_rot;
    gazebo_msgs::ModelState model_msg;
    geometry_msgs::Pose initPose;
    bool foundFlag = false;

public:
    void stateCallback(const vanttec_msgs::EtaPose& msg);
    void gazStateCallback(const gazebo_msgs::ModelStates::ConstPtr& msg);
};

void SetState::stateCallback(const vanttec_msgs::EtaPose& msg){
    // https://wiki.ros.org/action/show/geometry2/RotationMethods?action=show&redirect=geometry%2FRotationMethods
    model_msg.model_name = "vtec_u3";

    q.setRPY(msg.phi, msg.theta, msg.psi); // roll, pitch, yaw
    q.normalize();

    model_msg.pose.position.x = initPose.position.x + msg.x;
    model_msg.pose.position.y = initPose.position.y - msg.y;
    model_msg.pose.position.z = initPose.position.z - msg.z;

    model_msg.pose.orientation.x = q.x();
    model_msg.pose.orientation.y = q.y();
    model_msg.pose.orientation.z = q.z();
    model_msg.pose.orientation.w = q.w();

    pub_state.publish(model_msg);
}

void SetState::gazStateCallback(const gazebo_msgs::ModelStates::ConstPtr& msg){
    if(foundFlag == 0){
        for(int i=0; i<msg->name.size(); i++){
            if(msg->name[i] == "vtec_u3"){
                initPose.position = msg->pose[i].position;
                initPose.orientation = msg->pose[i].orientation;
                foundFlag = 1;
            }
        }
    }
}

int main(int argc, char **argv){
    ros::init(argc,argv, "gazebo_interface");
    SetState state;
    ros::spin();
    return 0;
}