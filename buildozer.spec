[app]
title = MU Online Offline
package.name = muonlineoffline
package.domain = com.game.muoffline
source.dir = .
source.include_exts = py,png,jpg,jpeg,ttf,atlas,json
version = 1.0

# Requirements - pygame-ce ho tro Android tot hon pygame
requirements = python3,pygame-ce

# Orientation ngang
orientation = landscape
fullscreen = 1

# Android settings
android.permissions = VIBRATE
android.api = 33
android.minapi = 21
android.ndk = 25b
android.archs = arm64-v8a,armeabi-v7a
android.allow_backup = True

# Icon (tuy chon)
# icon.filename = %(source.dir)s/assets/icon.png

[buildozer]
log_level = 2
warn_on_root = 1
