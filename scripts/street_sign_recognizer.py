#!/usr/bin/env python 

""" This is a script that walks through some of the basics of working with images
    with opencv in ROS. """

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np
from template_matcher import TemplateMatcher

class StreetSignRecognizer(object):
    """ This robot should recognize street signs """


    def __init__(self):
        """ Initialize the street sign reocgnizer """
        rospy.init_node('street_sign_recognizer')

        # Create TemplateMatcher object with template images
        self.template_matcher = TemplateMatcher(
            {
                "left":'../images/leftturn_box_small.png',
                "right":'../images/rightturn_box_small.png',
                "uturn":'../images/uturn_box_small.png'
            }
        )

        self.bgr_image = None                        # the latest image from the camera
        self.hsv_image = None
        self.filt_image = None
        self.cropped_sign_grayscale = None

        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV
        
        # Create windows to view video streams
        cv2.namedWindow('video_window')
        cv2.namedWindow('filt_window')
        cv2.namedWindow('cropped_grayscale_window')
        cv2.namedWindow('img_T_window')

        # Create sliders to control image color filtering
        cv2.namedWindow('threshold_image')
        self.h_lower_bound = 25
        self.h_upper_bound = 38
        self.s_lower_bound = 199
        self.s_upper_bound = 255
        self.v_lower_bound = 203
        self.v_upper_bound = 237
        self.blur_amount = 3
        cv2.createTrackbar('H lower bound', 'threshold_image', 0, 255, self.set_h_lower_bound)
        cv2.createTrackbar('H upper bound', 'threshold_image', 0, 255, self.set_h_upper_bound)
        cv2.createTrackbar('S lower bound', 'threshold_image', 0, 255, self.set_s_lower_bound)
        cv2.createTrackbar('S upper bound', 'threshold_image', 0, 255, self.set_s_upper_bound)
        cv2.createTrackbar('V lower bound', 'threshold_image', 0, 255, self.set_v_lower_bound)
        cv2.createTrackbar('V upper bound', 'threshold_image', 0, 255, self.set_v_upper_bound)
        cv2.createTrackbar('Blur amount', 'threshold_image', 0, 20, self.set_blur_amount)
        cv2.setTrackbarPos('H lower bound', 'threshold_image', self.h_lower_bound)
        cv2.setTrackbarPos('H upper bound', 'threshold_image', self.h_upper_bound)
        cv2.setTrackbarPos('S lower bound', 'threshold_image', self.s_lower_bound)
        cv2.setTrackbarPos('S upper bound', 'threshold_image', self.s_upper_bound)
        cv2.setTrackbarPos('V lower bound', 'threshold_image', self.v_lower_bound)
        cv2.setTrackbarPos('V upper bound', 'threshold_image', self.v_upper_bound)
        cv2.setTrackbarPos('Blur amount', 'threshold_image', self.blur_amount)

        # Subscribe to ROS image stream
        rospy.Subscriber("/camera/image_raw", Image, self.process_image)

    def set_h_lower_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the hue lower bound """
        self.h_lower_bound = val

    def set_h_upper_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the hue upper bound """
        self.h_upper_bound = val

    def set_s_lower_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the saturation lower bound """
        self.s_lower_bound = val

    def set_s_upper_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the saturation upper bound """
        self.s_upper_bound = val

    def set_v_lower_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the value lower bound """
        self.v_lower_bound = val

    def set_v_upper_bound(self, val):
        """ A callback function to handle the OpenCV slider to select the value upper bound """
        self.v_upper_bound = val

    def set_blur_amount(self, val):
        """ A callback function to handle the OpenCV slider to select the blur amount """
        # The kernel blur size must always be odd
        self.blur_amount = 2*val+1

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        # Convert ROS image stream to opencv image stream
        self.bgr_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        # Gaussian blur the image to low-pass contents
        self.blurred_bgr_image = cv2.GaussianBlur(self.bgr_image, \
            (self.blur_amount, self.blur_amount), 0)

        # Shift to HSV image and filter for color of traffic signs
        self.hsv_image = cv2.cvtColor(self.blurred_bgr_image, cv2.COLOR_BGR2HSV)
        self.filt_image = cv2.inRange(self.hsv_image, \
            (self.h_lower_bound, self.s_lower_bound, self.v_lower_bound),
            (self.h_upper_bound, self.s_upper_bound, self.v_upper_bound))

        # Define a bounding box around the detected color
        left_top, right_bottom = self.sign_bounding_box()
        left, top = left_top
        right, bottom = right_bottom
        cropped_sign = self.bgr_image[top:bottom, left:right]

        # Convert bounded image to grayscale and detect type of traffic sign
        self.cropped_sign_grayscale = cv2.cvtColor(cropped_sign, cv2.COLOR_BGR2GRAY)
        print self.template_matcher.predict(self.cropped_sign_grayscale)

        # Draw visual bounding box on bgr_image
        cv2.rectangle(self.bgr_image, left_top, right_bottom, color=(0, 0, 255), thickness=5)

    def sign_bounding_box(self):
        """
        Returns
        -------
        (left_top, right_bottom) where left_top and right_bottom are tuples of (x_pixel, y_pixel)
            defining topleft and bottomright corners of the bounding box
        """
        # Find contours based on the binary filtered image
        contours, hierarchy = cv2.findContours(self.filt_image, cv2.RETR_TREE, \
           cv2.CHAIN_APPROX_SIMPLE)

        # Define bounding rectangle around contour
        if (contours):
            x, y, w, h = cv2.boundingRect(contours[0])
            left_top = (x, y)
            right_bottom = (x+w, y+h)
            return left_top, right_bottom
        else:
            # If no contours were found
            return 0, 0

    def run(self):
        """ The main run loop"""
        r = rospy.Rate(10)
        while not rospy.is_shutdown():
            # Create windows to show all specified image streams
            if (not self.bgr_image is None):
                cv2.imshow('video_window', self.bgr_image)
            if (not self.filt_image is None):
                cv2.imshow('filt_window', self.filt_image)
            if (not self.cropped_sign_grayscale is None):
                cv2.imshow('cropped_grayscale_window', self.cropped_sign_grayscale)
            if (not self.template_matcher.img_T is None):
                cv2.imshow('img_T_window', self.template_matcher.img_T)
            cv2.waitKey(5)
            r.sleep()

if __name__ == '__main__':
    node = StreetSignRecognizer()
    node.run()
