
from PIL import Image, ImageDraw

image = Image.new("RGB", (900, 600), "#f3f4f6")
draw = ImageDraw.Draw(image)

draw.rectangle((0, 0, 900, 56), fill="#1f2937")
draw.text((24, 18), "Acme Dashboard", fill="white")

draw.rounded_rectangle((200, 110, 700, 510), radius=12, fill="white", outline="#d1d5db")
draw.text((240, 135), "Sign in", fill="#111827")
draw.text((240, 185), "Email", fill="#374151")
draw.rectangle((240, 205, 660, 249), fill="white", outline="#9ca3af")
draw.text((254, 219), "user@example.com", fill="#6b7280")

draw.text((240, 275), "Password", fill="#374151")
draw.rectangle((240, 295, 660, 339), fill="white", outline="#9ca3af")
draw.text((254, 309), "********", fill="#6b7280")

draw.rounded_rectangle((240, 365, 660, 413), radius=5, fill="#2563eb")
draw.text((425, 381), "Sign in", fill="white")
draw.text((240, 445), "Error: Unable to authenticate user", fill="#dc2626")

image.save("test-ui.png")
print("Created test-ui.png")
