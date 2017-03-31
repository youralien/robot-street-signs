#!/usr/bin/env python

""" This is a script that walks through some of the basics of working with images
    with opencv in ROS. """

import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

class StreetSignRecognizer(object):
    """ This robot should recognize street signs """


    def __init__(self):
        """ Initialize the street sign reocgnizer """
        rospy.init_node('street_sign_recognizer')
        self.cv_image = None                        # the latest image from the camera
        self.bridge = CvBridge()                    # used to convert ROS messages to OpenCV
        cv2.namedWindow('video_window')
        rospy.Subscriber("/camera/image_raw", Image, self.process_image)
        self.image_info_window = None
        cv2.setMouseCallback('video_window', self.process_mouse_event)

        self.binary_image = None
        cv2.namedWindow('binary_window')

        cv2.namedWindow('threshold_image')
        self.hsv_lb = np.array([25, 155, 145]) # hsv lower bound
        cv2.createTrackbar('H lb', 'threshold_image', 0, 255, self.set_h_lb)
        cv2.createTrackbar('S lb', 'threshold_image', 0, 255, self.set_s_lb)
        cv2.createTrackbar('V lb', 'threshold_image', 0, 255, self.set_v_lb)
        self.hsv_ub = np.array([50, 255, 255]) # hsv upper bound
        cv2.createTrackbar('H ub', 'threshold_image', 0, 255, self.set_h_ub)
        cv2.createTrackbar('S ub', 'threshold_image', 0, 255, self.set_s_ub)
        cv2.createTrackbar('V ub', 'threshold_image', 0, 255, self.set_v_ub)

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        self.hsv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")
        left_top, right_bottom = self.sign_bounding_box()
        left, top = left_top
        right, bottom = right_bottom

        # crop bounding box region of interest
        cropped_sign = self.cv_image[top:bottom, left:right]

        # draw bounding box rectangle
        cv2.rectangle(self.cv_image, left_top, right_bottom, color=(0, 0, 255), thickness=5)
        cv2.imshow('binary_window', self.binary_image)
        cv2.imshow('video_window', self.cv_image)


    def sign_bounding_box(self):
        """
        Returns
        -------
        (left_top, right_bottom) where left_top and right_bottom are tuples of (x_pixel, y_pixel)
            defining topleft and bottomright corners of the bounding box
        """
        self.binary_image = cv2.inRange(self.hsv_image, self.hsv_lb, self.hsv_ub)
        top = 480
        left = 640
        bottom = 0
        right = 0
        for x in range (0, 480):
            for y in range(0, 640):
                if self.binary_image[x, y] != 0:
                    if x < top :
                        top = x
                    if x > bottom:
                        bottom = x
                    if y < left:
                        left = y
                    if y > right:
                        right = y
        left_top = (left, top)
        right_bottom = (right, bottom)
        return left_top, right_bottom

    def run(self):
        """ The main run loop"""
        r = rospy.Rate(10)
        while not rospy.is_shutdown():
            if not self.image_info_window is None:
                cv2.imshow('image_info', self.image_info_window)
                cv2.waitKey(5)
            if not self.cv_image is None:
                print "here"
                # creates a window and displays the image for X milliseconds
                cv2.waitKey(5)
            r.sleep()

    def process_mouse_event(self, event, x,y,flags,param):
        """ Process mouse events so that you can see the color values associated
            with a particular pixel in the camera images """
        self.image_info_window = 255*np.ones((500,500,3))

        # show hsv values
        cv2.putText(self.image_info_window,
                    'Color (h=%d,s=%d,v=%d)' % (self.hsv_image[y,x,0], self.hsv_image[y,x,1], self.hsv_image[y,x,2]),
                    (5,50), # 5 = x, 50 = y
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,0))

        # show bgr values
        cv2.putText(self.image_info_window,
                    'Color (b=%d,g=%d,r=%d)' % (self.cv_image[y,x,0], self.cv_image[y,x,1], self.cv_image[y,x,2]),
                    (5,100),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    (0,0,0))

    def set_h_lb(self, val):
        """ set hue lower bound """
        self.hsv_lb[0] = val

    def set_s_lb(self, val):
        """ set saturation lower bound """
        self.hsv_lb[1] = val

    def set_v_lb(self, val):
        """ set value lower bound """
        self.hsv_lb[2] = val

    def set_h_ub(self, val):
        """ set hue upper bound """
        self.hsv_ub[0] = val

    def set_s_ub(self, val):
        """ set saturation upper bound """
        self.hsv_ub[1] = val

    def set_v_ub(self, val):
        """ set value upper bound """
        self.hsv_ub[2] = val

if __name__ == '__main__':
    node = StreetSignRecognizer()
    node.run()
