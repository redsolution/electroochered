# -*- coding: utf-8 -*-

from imagekit import processors
from imagekit.specs import ImageSpec
from attachment.settings import ATTACHMENT_DISPLAY_QUALITY

class ResizeDisplay(processors.Resize):
    width = 80
    height = 80

class Display(ImageSpec):
    quality = ATTACHMENT_DISPLAY_QUALITY
    processors = [ResizeDisplay, ]

class ThumbDisplay(processors.Resize):
    width = 80
    height = 80

class Thumb(ImageSpec):
    pre_cache = True
    processors = [ThumbDisplay, ]