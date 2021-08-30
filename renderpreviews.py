from PIL import Image
from colorsys import hsv_to_rgb
from ledcontrol.animationcontroller import AnimationController
import ledcontrol.animationpatterns as animpatterns
import ledcontrol.colorpalettes as colorpalettes
import ledcontrol.pixelmappings as pixelmappings
import ledcontrol.driver as driver
import ledcontrol.utils as utils

controller = AnimationController(None, 0, 256, pixelmappings.line(256), (0, 0, 0), False)

s = 150
t = 800

'''
pattern_dict = animpatterns.default[151]
errors, warnings, pattern = controller.compile_pattern(pattern_dict['source'])

img = Image.new('RGB', (t, s), 'black')
pixels = img.load()

print(pattern_dict["name"])

prev = [(0, 0, 0) for i in range(s)]
for i in range(img.size[0]):
    for j in range(img.size[1]):
        p = pattern((pattern_dict['primary_speed'] / 0.2) * float(i) / float(s), 1.0 / s, float(j) / float(s), 0, prev[j])
        prev[j] = p[0]
        if p[1] == animpatterns.ColorMode.hsv:
            pixels[i, j] = tuple([int(x * 255) for x in hsv_to_rgb(*p[0])])
        else:
            pixels[i, j] = tuple([int(x * 255) for x in p[0]])

img.save(f'test.png')
'''

f = open('patterns.md', 'w')
f.write('## Built-In Animation Patterns\n\nIn the images below, the y-axis represents the colors of a linear array of LEDs and the x-axis represents time.\n\n')

for pattern_dict in animpatterns.default.values():
    errors, warnings, pattern = controller.compile_pattern(pattern_dict['source'])

    img = Image.new('RGB', (t, s), 'black')
    pixels = img.load()

    print(pattern_dict["name"])
    f.write(f'## {pattern_dict["name"]}\n')

    prev = [(0, 0, 0) for i in range(s)]
    for i in range(img.size[0]):
        for j in range(img.size[1]):
            p = pattern((pattern_dict['primary_speed'] / 0.2) * i / s, 1.0 / s, j / s, 0, prev[j])
            prev[j] = p[0]
            if p[1] == animpatterns.ColorMode.hsv:
                pixels[i,j] = tuple([int(x * 255) for x in hsv_to_rgb(*p[0])])
            else:
                pixels[i,j] = tuple([int(x * 255) for x in p[0]])

    fn = f'img/{pattern_dict["name"]}.png'.replace(' ', '-')
    img.save(fn)
    f.write(f'![{fn}]({fn})\n\n')

f.close()
