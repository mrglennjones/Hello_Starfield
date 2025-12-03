import time
from random import randrange, uniform, random

import plasma

# -----------------------------
# CONFIG
# -----------------------------

NUM_LEDS = 66

# --- Starfield (background) ---

# Overall brightness range for stars
STAR_MIN_BRIGHT = 0.02     # very dim
STAR_MAX_BRIGHT = 0.8      # brightest "hero" stars

# How fast stars change brightness (lower = smoother, slower twinkle)
STAR_FADE_SPEED = 0.01     # change per frame towards target

# How often we pick a new "target" brightness per star (probability per frame)
STAR_NEW_TARGET_CHANCE = 0.01   # 1% chance per star per frame

# Slight colour variation so "white" isn't dead flat (looks nicer)
STAR_SATURATION_MAX = 0.05  # 0.0 = pure white, up to 0.05 still looks mostly white
STAR_HUE_SPREAD = 20        # degrees around 220° (cool white / very pale blue)

# Base frame speed for star twinkling
TWINKLE_FRAME_DELAY = 0.05  # seconds between frames (~20 FPS)


# --- Comets ---

# Roughly how often a comet appears (probability per twinkle frame).
# Tuned to be nicely rare now.
COMET_BASE_CHANCE = 0.00015

COMET_MIN_TRAIL = 3
COMET_MAX_TRAIL = 8

COMET_MIN_SPEED = 0.015     # faster comet
COMET_MAX_SPEED = 0.035     # slower comet

COMET_HEAD_BRIGHT_MIN = 0.6
COMET_HEAD_BRIGHT_MAX = 1.0

# How much brighter than the background a comet can "burn in" as afterglow
AFTERGLOW_MAX = 0.4

# Comet colour (cool white / very pale blue)
COMET_HUE = 220 / 360.0     # bluish white
COMET_SAT = 0.1             # keep low so it still feels mostly white


# -----------------------------
# SETUP
# -----------------------------

# Your LED strip order as B → G → R, so use BGR order:
led_strip = plasma.WS2812(
    NUM_LEDS,
    color_order=plasma.COLOR_ORDER_BGR
)

led_strip.start()

# Star state per LED
star_current = [0.0] * NUM_LEDS      # current brightness
star_target = [0.0] * NUM_LEDS       # target brightness
star_hue = [0.0] * NUM_LEDS          # subtle hue variation
star_sat = [0.0] * NUM_LEDS          # subtle saturation variation


def random_star_brightness():
    """Return a brightness value with many dim stars and few bright ones."""
    # Square the uniform value to bias towards lower brightnesses:
    # 0–1 -> 0–1 but with more values near 0.
    x = uniform(0.0, 1.0)
    x = x * x
    return STAR_MIN_BRIGHT + x * (STAR_MAX_BRIGHT - STAR_MIN_BRIGHT)


def init_stars():
    """Initialise all stars with random brightness and slight colour variation."""
    for i in range(NUM_LEDS):
        b = random_star_brightness()
        star_current[i] = b
        star_target[i] = random_star_brightness()

        # hue around a cool white (220°), ±STAR_HUE_SPREAD/2
        hue_offset_deg = uniform(-STAR_HUE_SPREAD / 2, STAR_HUE_SPREAD / 2)
        star_hue[i] = (220 + hue_offset_deg) / 360.0

        # tiny bit of saturation so it's not dead flat
        star_sat[i] = uniform(0.0, STAR_SATURATION_MAX)


def update_stars():
    """Move each star towards its target brightness and occasionally choose a new one."""
    for i in range(NUM_LEDS):
        # Occasionally choose a new random target brightness
        if random() < STAR_NEW_TARGET_CHANCE:
            star_target[i] = random_star_brightness()

        # Smoothly ease current brightness towards target
        cur = star_current[i]
        tgt = star_target[i]

        if cur < tgt:
            cur += STAR_FADE_SPEED
            if cur > tgt:
                cur = tgt
        elif cur > tgt:
            cur -= STAR_FADE_SPEED
            if cur < tgt:
                cur = tgt

        star_current[i] = cur

        # Draw star
        led_strip.set_hsv(i, star_hue[i], star_sat[i], cur)


def run_comet():
    """Animate a single comet gliding across the strip."""
    trail_len = randrange(COMET_MIN_TRAIL, COMET_MAX_TRAIL + 1)
    if trail_len > NUM_LEDS:
        trail_len = NUM_LEDS

    # Random direction
    direction = 1 if randrange(2) == 0 else -1

    # Random speed and head brightness for variety
    comet_delay = uniform(COMET_MIN_SPEED, COMET_MAX_SPEED)
    head_brightness = uniform(COMET_HEAD_BRIGHT_MIN, COMET_HEAD_BRIGHT_MAX)

    if direction == 1:
        head = -trail_len
        end = NUM_LEDS + trail_len
        step = 1
    else:
        head = NUM_LEDS + trail_len
        end = -trail_len
        step = -1

    while head != end:
        # Draw background first
        for i in range(NUM_LEDS):
            led_strip.set_hsv(i, star_hue[i], star_sat[i], star_current[i])

        # Draw comet on top
        for k in range(trail_len):
            pos = head - k * direction
            if 0 <= pos < NUM_LEDS:
                # Fraction along tail: 0 at the end, 1 at the head
                frac = (trail_len - k) / float(trail_len)
                # Use squared falloff for a bright head, smooth tail
                comet_b = head_brightness * (frac * frac)

                # Slight colour gradient: head more coloured, tail whiter
                tail_sat = COMET_SAT * frac   # more saturated at head
                tail_hue = COMET_HUE

                led_strip.set_hsv(pos, tail_hue, tail_sat, comet_b)

                # Gentle afterglow: boost star brightness a little, but keep within range
                glow_boost = comet_b * AFTERGLOW_MAX
                new_star_b = min(star_current[pos] + glow_boost, STAR_MAX_BRIGHT)
                star_current[pos] = new_star_b

        time.sleep(comet_delay)
        head += step


# -----------------------------
# MAIN LOOP
# -----------------------------

init_stars()

while True:
    # Update starfield
    update_stars()

    # Occasionally launch a comet
    # Slight randomness in chance by modulating with a tiny extra factor
    comet_chance = COMET_BASE_CHANCE * uniform(0.5, 1.5)
    if random() < comet_chance:
        run_comet()

    time.sleep(TWINKLE_FRAME_DELAY)
