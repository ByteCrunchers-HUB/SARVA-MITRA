from PIL import Image
p = "/mnt/c/Users/Vijay Karthik/.gemini/antigravity/brain/a90e6c9e-b932-4c93-845f-744f5073ae79/.user_uploaded/media_1795517214009_a82ea6cf.png"
im = Image.open(p)
print("Uploaded image:", im.size, im.format, im.mode)
