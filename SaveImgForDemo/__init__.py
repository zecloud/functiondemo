import logging

import azure.functions as func
from PIL import Image, ImageDraw, ImageFont
import io

def main(myblob: bytes,outputBlob:func.Out[func.InputStream]):

    image = Image.open(io.BytesIO(myblob))
    width, height = image.size

    draw = ImageDraw.Draw(image)
    text = "Gangogh by ZeCloud"

    font = ImageFont.truetype('Vincent.ttf', 36)
    textwidth, textheight = draw.textsize(text, font)

    # calculate the x,y coordinates of the text
    margin = 10
    x = width - textwidth - margin
    y = height - textheight - margin

    # draw watermark in the bottom right corner
    draw.text((x, y), text, font=font)
    image.show()
    if image.mode in ('RGBA', 'LA'):
        fill_color = '#FFFFFF'  # your background
        background = Image.new(image.mode[:-1], image.size, fill_color)
        background.paste(image, image.split()[-1])
        image = background
    dataout = io.BytesIO()
    image.save(dataout,'jpeg')
    dataout.seek(0)
    outputBlob.set(dataout)

    
