# -*- coding: utf-8 -*-
import gnupg


def sign_is_valid(data):
    gpg = gnupg.GPG()
    return gpg.verify(data)


def make_sign(data):
    gpg = gnupg.GPG()
    return gpg.sign(str(data))
