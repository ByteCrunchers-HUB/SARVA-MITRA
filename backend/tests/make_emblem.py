from PIL import Image, ImageDraw

def create_rounded_emblem():
    # Load original compact logo
    src_path = "/home/vijay/git/SARVA-MITRA/frontend/assets/logo-compact.png"
    im = Image.open(src_path).convert("RGBA")
    
    # Resize to clean 256x256
    size = (256, 256)
    im = im.resize(size, Image.Resampling.LANCZOS)
    
    # Create smooth antialiased rounded corner mask
    # Scale 4x for supersampling
    scale = 4
    mask_size = (size[0] * scale, size[1] * scale)
    mask = Image.new("L", mask_size, 0)
    draw = ImageDraw.Draw(mask)
    
    # 54px corner radius at 256px
    radius = int(54 * scale)
    draw.rounded_rectangle([(0, 0), (mask_size[0] - 1, mask_size[1] - 1)], radius=radius, fill=255)
    
    # Downsample mask
    mask = mask.resize(size, Image.Resampling.LANCZOS)
    
    # Apply mask
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    out.paste(im, (0, 0), mask=mask)
    
    dst_path = "/home/vijay/git/SARVA-MITRA/frontend/assets/logo-emblem.png"
    out.save(dst_path, "PNG")
    print(f"Saved {dst_path} with smooth rounded corners! Size: {out.size}")

if __name__ == "__main__":
    create_rounded_emblem()
