#!/bin/bash

set -CEuo pipefail
SCRIPT_DIR=$(cd $(dirname $0) && pwd)
cd ${SCRIPT_DIR}

label='日本語\n\nMake an image with text\nby using ImageMagick'
background_color='#000000'
icon_sizeW=512
# icon_ratio=1.777
icon_ratio=`echo "scale=5; 16 / 9" | bc`
border=20
font='.Hiragino-Kaku-Gothic-Interface-W4'
color='#FFFFFF'

file_name="icon.png"
sizeW=`echo "scale=0; $icon_sizeW - $border * 2" | bc`
sizeH=`echo "scale=0; $icon_sizeW / $icon_ratio - $border * 2" | bc`

convert \
	-size "${sizeW}x${sizeH}" -background $background_color \
	-fill $color -font $font -gravity center label:"$label" \
	-bordercolor $color -border $border \
	$file_name