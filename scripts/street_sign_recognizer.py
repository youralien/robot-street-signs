#!/usr/bin/env python

""" This is a script that walks through some of the basics of working with images
    with opencv in ROS. """

import time
import rospy
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
import cv2
import numpy as np

from template_matcher import defaultMatcher


class StreetSignRecognizer(object):
    """ This robot should recognize street signs """

    def __init__(self):
        """ Initialize the street sign reocgnizer """
        rospy.init_node('street_sign_recognizer')
        self.cv_image = None  # the latest image from the camera
        self.hsv_img = None
        self.binary_img = None
        self.bridge = CvBridge()  # used to convert ROS messages to OpenCV
        cv2.namedWindow('video_window')
        cv2.namedWindow('HSV_window')
        cv2.namedWindow('binary_window')
        rospy.Subscriber("/camera/image_raw", Image, self.process_image)

        self.buffer_size = 30  # pixels

        self.hsv_min = np.array((20, 200, 200))
        self.hsv_max = np.array((40, 255, 255))

        self.make_multi_slider(self.hsv_min, "min ")
        self.make_multi_slider(self.hsv_max, "max ")

        self.recognizer = defaultMatcher()


    @staticmethod
    def make_multi_slider(array, prefix="", window='binary_window', names='H S V'.split(), max=255):
        assert len(array) == len(names)

        def make_callback(local_i):
            def cb(val):
                array[local_i] = val
            return cb

        for i in range(len(array)):
            cv2.createTrackbar(prefix + names[i], window, array[i], max, make_callback(i))

    def process_image(self, msg):
        """ Process image messages from ROS and stash them in an attribute
            called cv_image for subsequent processing """
        self.cv_image = self.bridge.imgmsg_to_cv2(msg, desired_encoding="bgr8")

        left_top, right_bottom = self.sign_bounding_box()
        left, top = left_top
        right, bottom = right_bottom

        if right > 0:
            # draw bounding box rectangle
            cv2.rectangle(self.cv_image, left_top, right_bottom, color=(0, 0, 255), thickness=5)

            # crop bounding box region of interest
            cropped_sign = self.cv_image[top:bottom, left:right]

            cropped_gray = cv2.cvtColor(cropped_sign, cv2.COLOR_BGR2GRAY)

            # self.binary_img = cropped_gray

            # Detect which sign this is
            probs = self.recognizer.predict(cropped_gray)

            print "Image identified as {} with chance {}".format(max(probs, key=lambda k: probs[k]), max(probs.values()))
        else:
            print "No bounding box found"


    def sign_bounding_box(self):
        """
        Returns
        -------
        (left_top, right_bottom) where left_top and right_bottom are tuples of (x_pixel, y_pixel)
            defining topleft and bottomright corners of the bounding box
        """
        self.hsv_img = cv2.cvtColor(self.cv_image, cv2.COLOR_BGR2HSV)

        self.binary_img = cv2.inRange(self.hsv_img, self.hsv_min, self.hsv_max)

        binary_image_copy = np.copy(self.binary_img)

        im2, contours, hierarchy = cv2.findContours(binary_image_copy, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            return (0, 0), (0, 0)

        # Find the largest contour
        contour = max(contours, key=cv2.contourArea)

        x, y, w, h = cv2.boundingRect(contour)

        cv2.drawContours(self.hsv_img, [contour], 0, (255, 0, 9), thickness=5)

        left_top = [x - self.buffer_size, y - self.buffer_size]
        right_bottom = [x + w + self.buffer_size, y + h + self.buffer_size]

        left_top[0] = max(left_top[0], 1)
        return tuple(left_top), tuple(right_bottom)

    def run(self):
        """ The main run loop"""
        while not rospy.is_shutdown():
            if self.cv_image is not None:
                # creates a window and displays the image for X milliseconds
                cv2.imshow('video_window', self.cv_image)
                cv2.imshow('HSV_window', self.hsv_img)
                cv2.imshow('binary_window', self.binary_img)
                cv2.waitKey(5)

            time.sleep(0.1)


if __name__ == '__main__':
    node = StreetSignRecognizer()
    node.run()
