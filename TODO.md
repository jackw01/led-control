### Core Features
#### 2018-10
- [x] web interface
- [x] dynamically generated control form - arbitrary parameters
- [x] animation thread with proper waiting between cycles
- [x] time and space dependent animations
- [x] basic animations - hue cycle
- [x] brightness and saturation control
- [x] basic secondary animations with scaling
- [x] both number and slider inputs on UI
- [x] command line arguments for configuration
- [x] color palette UI with color pickers
- [x] save/load animation params and colors

#### 2019-08
- [x] rework animation controller to compute mappings better
- [x] make patterns and mappings functions
- [x] animation time profiling
- [x] support all possible pixel orders and sk6812
- [x] test alternative color conversions in python
- [x] LED color correction
- [x] color temperature control
- [x] make form generator code more pythonic
- [x] web UI - migrate to SCSS
- [x] web UI - flexbox
- [x] web UI - update style
- [x] support HSV and RGB modes in pattern functions
- [x] secondary patterns as functions
- [x] make scale input more intuitive
- [x] rewrite color conversion and LED output code in C
- [x] rewrite color correction and temperature in C
- [x] compile patterns with RestrictedPython
- [x] web UI - code editor
- [x] web UI - load pattern source code
- [x] web UI - display compile errors
- [x] utility functions for restricted environment

#### 2019-09
- [x] save edited patterns
- [x] web UI - allow inverting pattern scale
- [x] web UI - update number inputs when sliders are moved
- [x] rewrite final saturation/brightness in C
- [x] apply saturation in RGB render mode
- [x] web UI - prevent editing default patterns
- [x] web UI - copying and renaming patterns
- [x] web UI - better color pickers
- [x] web UI - secondary pattern menu
- [x] more secondary patterns
- [x] rewrite blackbody conversions in C
- [x] rewrite all wave/utility functions in C
- [x] calculate pixel mappings and scale once and store them
- [x] optimize animation loop with list comprehensions
- [x] RGB plasma shader and utility function
- [x] perlin noise utility function

#### 2019-10
- [x] automatically save settings
- [x] general code cleanup and documentation
- [x] brightness limiting
- [x] secondary patterns - wipe
- [x] web UI - update code after changing patterns
- [x] patterns - ripple
- [x] patterns - hsv waves

### Extras
- [x] SK6812 RGBW support
- [x] per-pattern speed/scale
- [x] delete pattern
- [X] gradient/palette based patterns
- [X] web UI palette picker
- [x] web UI palette selection
- [x] web UI palette create/rename
- [x] web UI palette delete
- [x] web UI palette add/remove colors
- [x] update existing hsv patterns to palettes
- [x] palette - multi color wipe/bands
- [x] palette - ripples
- [x] palette - random wipe

### Extras 2
- [x] better default palettes
- [x] palette based - plasma
- [x] DMX
- [x] render animations to images for readme
- [x] add palette_mirrored utility for performance
- [x] pixel mapping
- [x] 3D
- [ ] timer
- [ ] pixel mapping global rotation/scale
- [ ] pixel mapping editor

sudo ledcontrol --led_count 150 --led_pixel_order GRBW --led_color_correction "#FFA8FF"
