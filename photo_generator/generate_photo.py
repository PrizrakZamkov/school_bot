from PIL import Image, ImageDraw, ImageFont


def get_photo(text=''):
    try:
        image = Image.open("photo_generator\photo.jpg")

        font = ImageFont.truetype('arial.ttf', size=23)
        draw_text = ImageDraw.Draw(image)
        draw_text.text(
            (300, 325),
            text,
            font=font,
            fill=('#1C0606')
        )
        # image.show()
        new_name = text.split(" ")[1]
        image.save(rf'new_photos\timetable_photo_{new_name}.jpg')
        return rf'new_photos\timetable_photo_{new_name}.jpg'
    except:
        return "photo_generator\photo.jpg"
