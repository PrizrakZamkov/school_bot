from PIL import Image, ImageDraw, ImageFont


def get_photo(text=''):
    try:
        text = text[2:]  # убираем эмодзи и пробел
        name = text.split(" ")[0]
        day = text.split(" ")[1][:-1]  # до :
        try:
            Image.open(rf'timetable_photo_{name}_{day}.jpg')
        except:
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
            image.save(rf'new_photos\timetable_photo_{name}_{day}.jpg')
        return rf'new_photos\timetable_photo_{name}_{day}.jpg'
    except Exception as ex:
        print(ex)
        return "photo_generator\photo.jpg"
