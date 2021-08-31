from PIL import Image
from colorsys import hsv_to_rgb
from ledcontrol.animationcontroller import AnimationController
import ledcontrol.animationpatterns as animpatterns
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.pixelmappings as pixelmappings
import ledcontrol.driver as driver
import ledcontrol.utils as utils

controller = AnimationController(None, 0, 256, pixelmappings.line(256), (0, 0, 0), False)

s = 100 # LED strip length
t = 400 # Time units
gif_t = 300 # Animated gif duration

f = open('patterns.md', 'w')
f.write('## Built-In Animation Patterns\n\n')

for pattern_dict in animpatterns.default.values():
    errors, warnings, pattern = controller.compile_pattern(pattern_dict['source'])

    img = Image.new('RGB', (t, s), 'black')
    pixels = img.load()

    print(pattern_dict["name"])
    f.write(f'## {pattern_dict["name"]}\n')

    prev = [(0, 0, 0) for i in range(s)]

    frames = []

    for i in range(img.size[0]):
        frame = Image.new('RGB', (s, 1), 'black')
        frame_pixels = frame.load()
        for j in range(img.size[1]):
            p = pattern((pattern_dict['primary_speed'] / 0.2) * i / s, 1.0 / s, j / s, 0, 0, prev[j])
            prev[j] = p[0]
            if p[1] == animpatterns.ColorMode.hsv:
                c = tuple([int(x * 255) for x in hsv_to_rgb(*p[0])])
                pixels[i, j] = c
                frame_pixels[j, 0] = c
            else:
                c = tuple([int(x * 255) for x in p[0]])
                pixels[i, j] = c
                frame_pixels[j, 0] = c
        if i < gif_t:
            frames.append(frame)

    #img_name = f'img/{pattern_dict["name"]}.png'.replace(' ', '-')
    gif_name = f'img/{pattern_dict["name"]}.gif'.replace(' ', '-')
    #img.save(img_name)
    frames[0].save(gif_name, save_all=True, append_images=frames[1:], duration=100, loop=0)
    f.write(f'<img src="{gif_name}" width="800"/>\n\n')
    #f.write(f'<img src="{img_name}" width="800"/>\n\n')

f.close()
