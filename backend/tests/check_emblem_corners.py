from PIL import Image
p = "/home/vijay/git/SARVA-MITRA/frontend/assets/logo-emblem.png"
im = Image.open(p)
print("emblem size:", im.size, im.mode)
print("corner (0,0):", im.getpixel((0,0)))
print("corner (255,0):", im.getpixel((255,0)))
print("corner (0,255):", im.getpixel((0,255)))
print("corner (255,255):", im.getpixel((255,255)))
