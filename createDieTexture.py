import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import os
import string

# Paths
template_path = r"C:\Program Files (x86)\Steam\steamapps\common\Tabletop Simulator\Modding\Dice Templates\d6.png"
output_dir = "custom_dice_letters"
os.makedirs(output_dir, exist_ok=True)

scrabble_scores = {
    "A": 1, "E": 1, "I": 1, "O": 1, "U": 1,           # Vowels (Group 1)
    "L": 2, "N": 2, "S": 2, "T": 2, "R": 2,           # Low consonants (Group 2)
    "B": 3, "C": 3, "M": 3, "P": 3,                   # Mid-tier melee (Group 3)
    "D": 4, "G": 4, "V": 4, "Y": 4,                   # Mid-tier ranged (Group 4)
    "F": 5, "H": 5, "W": 5,                           # Rare-ish (Group 5)
    "J": 6, "X": 6, "K": 6,                           # High-tier attackers (Group 6)
    "Q": 7, "Z": 7                                    # Elite attackers (Group 7)
}




scrabble_colors = {
    1: (40, 160, 100),     # Vowels - Evergreen Green 🌲
    2: (80, 160, 255),     # Low Consonants - Sky Blue
    3: (200, 100, 60),     # Mid-tier Melee - Burnt Sienna 🪓
    4: (255, 185, 80),     # Mid-tier Ranged - Warm Gold 🏹
    5: (150, 50, 255),     # Rare-ish - Royal Purple
    6: (220, 50, 180),     # High Attack - Magenta
    7: (255, 70, 0),       # Elite Attack - Lava Red
}



dice_faces = {
    1: [  # Vowels: Movement-focused
        "MV:2", "MV:2", "MV:1", "MV:1", "MV:1", "S:0.5"
    ],
    2: [  # Low consonants: Light defense
        "S:2", "S:1", "S:1", "S:1", "MV:1", "MV:1"
    ],
    3: [  # Mid-tier melee
        "M:2", "M:1", "M:1", "S:1", "S:1", "MV:0.5"
    ],
    4: [  # Mid-tier ranged (slightly boosted damage)
        "R:2", "R:2", "R:1", "S:0.5", "S:0.5", "MV:0.5"
    ],
    5: [  # Heavy weapons (flexible damage)
        "R:2", "R:1", "HX:2", "M:2", "M:2", "HX:1"
    ],
    6: [  # Exotic mix (now with hybrid damage)
        "NG:1", "NG:2", "HX:2", "HX:2", "RE:2", "RE:2"
    ],
    7: [  # Fully exotic
        "NG:2", "NG:2", "MP:2", "MP:2", "RE:2", "HX:3"
    ]
}








# Load and convert
img_bgr = cv2.imread(template_path)
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
img_gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
img_height, img_width = img_gray.shape

# Threshold for light regions (die faces)
_, thresh_faces = cv2.threshold(img_gray, 250, 255, cv2.THRESH_BINARY)

# Find outer contours of die faces
contours, _ = cv2.findContours(thresh_faces, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
face_boxes = [cv2.boundingRect(c) for c in contours if cv2.contourArea(c) > 500]

# Compute average face width and height
avg_face_w = int(np.mean([w for (_, _, w, _) in face_boxes]))
avg_face_h = int(np.mean([h for (_, _, _, h) in face_boxes]))

# Letter size = half of face size
letter_w = avg_face_w // 2
letter_h = avg_face_h // 2

# Load font
font_path = "C:/temp/CuneiformFont/CUNEIFOR.TTF"
font_size = int(min(letter_w, letter_h) * 0.8)  # Slightly smaller
try:
    base_font = ImageFont.truetype(font_path, size=font_size)
except:
    base_font = ImageFont.load_default()
    print("⚠️ Default font used. For best results, specify a TTF font in font_path.")

# Pre-render letters at fixed size, centered with underline
letter_images = {}
for letter in string.ascii_uppercase:
    letter_img = Image.new("RGBA", (letter_w, letter_h), (255, 255, 255, 0))
    draw = ImageDraw.Draw(letter_img)

    bbox = draw.textbbox((0, 0), letter, font=base_font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = (letter_w - tw) // 2
    ty = (letter_h - th) // 2

    # Draw centered letter
    draw.text((tx, ty), letter, font=base_font, fill=(0, 0, 0, 255))

    # Underline at bottom of image
    underline_y = letter_h - 5
    draw.line([(40, underline_y), (letter_w - 40, underline_y)], fill=(0, 0, 0, 255), width=5)

    letter_images[letter] = letter_img

# Identify bottom-left and bottom-right faces
def distance(p1, p2):
    return np.linalg.norm(np.array(p1) - np.array(p2))

face_centers = [((x + w // 2), (y + h // 2)) for (x, y, w, h) in face_boxes]
bottom_left_corner = (0, img_height)
bottom_right_corner = (img_width, img_height)

bl_index = np.argmin([distance(center, bottom_left_corner) for center in face_centers])
br_index = np.argmin([distance(center, bottom_right_corner) for center in face_centers])

# Create output for each letter
img_pil_base = Image.fromarray(img_rgb).convert("RGBA")

for letter in string.ascii_uppercase:
    score = scrabble_scores[letter]
    color = scrabble_colors[score]
    img_pil = img_pil_base.copy()
    draw = ImageDraw.Draw(img_pil)
    letter_img = letter_images[letter]

    for i, (x, y, w, h) in enumerate(face_boxes):
        # Fill the full die face with the background color
        draw.rectangle([x, y, x + w, y + h], fill=color + (255,))

        # Center letter in the face box
        center_x = x + w // 2
        center_y = y + h // 2
        paste_x = int(center_x - letter_w / 2)
        paste_y = int(center_y - letter_h / 2)

        # Flip if bottom-left or bottom-right
        rotated_letter = letter_img.rotate(180) if i in [bl_index, br_index] else letter_img

        # Paste letter
        img_pil.paste(rotated_letter, (paste_x, paste_y), rotated_letter)

    # Save output
    out_path = os.path.join(output_dir, f"d6_{letter}.png")
    img_pil.save(out_path)
    print(f"✅ Saved {out_path}")
