from PIL import Image
p = "/mnt/c/Users/Vijay Karthik/.gemini/antigravity/brain/a90e6c9e-b932-4c93-845f-744f5073ae79/.user_uploaded/media_1795517214009_a82ea6cf.png"
im = Image.open(p)
print("Pixel at (0,0):", im.getpixel((0,0)))
print("Pixel at (497, 476):", im.getpixel((497, 476)))
print("Pixel at (250, 240):", im.getpixel((250, 240)))
