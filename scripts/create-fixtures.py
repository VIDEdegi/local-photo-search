"""Procedural fixtures, not real photos; generated only under data/fixtures."""
from PIL import Image, ImageDraw
from pathlib import Path
import random
root=Path(__file__).resolve().parents[1]/'data'/'fixtures'
random.seed(42)
for folder in ['objects','landscapes']:
    (root/folder).mkdir(parents=True,exist_ok=True)
# Still life: red apples on a wooden table.
im=Image.new('RGB',(640,480),(225,218,190)); d=ImageDraw.Draw(im)
d.rectangle((0,300,640,480),fill=(131,81,48))
for y in range(302,480,13): d.line((0,y,640,y),fill=(111,64,36),width=2)
d.ellipse((120,340,540,448),fill=(76,43,28))
for x,y,r in [(230,275,86),(395,294,74),(320,352,68)]:
    d.ellipse((x-r,y-r,x+r,y+r),fill=(163,24,26));d.ellipse((x-r+9,y-r+3,x+r-5,y+r-8),fill=(209,38,34))
    d.ellipse((x-r+20,y-r+20,x-r+48,y-r+50),fill=(248,111,86)); d.line((x,y-r+14,x+5,y-r-22),fill=(80,54,23),width=9)
    d.ellipse((x+2,y-r-25,x+50,y-r-3),fill=(62,119,36))
im.save(root/'objects'/'still-life.jpg',quality=94)
# Seaside with sandy beach, horizon, clouds and a sailboat.
im=Image.new('RGB',(640,480),(126,198,244)); d=ImageDraw.Draw(im)
for x,y in [(75,80),(300,40),(470,105)]:
    for dx,dy,r in [(0,0,30),(35,-9,40),(75,0,32)]:d.ellipse((x+dx-r,y+dy-r,x+dx+r,y+dy+r),fill=(247,249,249))
d.rectangle((0,220,640,400),fill=(32,133,183)); d.polygon([(0,350),(260,430),(640,290),(640,480),(0,480)],fill=(229,210,157))
for y in range(230,390,17):d.line((0,y,640,y),fill=(90,183,214),width=2)
d.polygon([(390,302),(472,302),(452,318),(409,318)],fill=(87,51,30));d.line((430,240,430,303),fill=(100,67,40),width=4);d.polygon([(426,242),(426,293),(393,293)],fill=(255,255,247));d.polygon([(435,250),(435,294),(469,294)],fill=(252,248,233))
im.save(root/'landscapes'/'coast.png')
# Dense forest and path.
im=Image.new('RGB',(640,480),(121,167,132));d=ImageDraw.Draw(im)
d.rectangle((0,240,640,480),fill=(56,91,46));d.polygon([(305,255),(348,255),(500,480),(110,480)],fill=(150,128,86))
for x,y,h in [(42,400,390),(145,330,285),(230,275,208),(390,290,240),(510,350,300),(610,420,400)]:
    d.rectangle((x-10,y-h,x+10,y),fill=(80,58,35))
    for i in range(4):d.polygon([(x,y-h-40+i*35),(x-70,y-h+120+i*35),(x+70,y-h+120+i*35)],fill=(24+7*i,70+10*i,37+4*i))
im.save(root/'landscapes'/'woodland.webp',quality=94)
# Urban skyline, roads, windows.
im=Image.new('RGB',(640,480),(166,198,213));d=ImageDraw.Draw(im)
for x,w,h in [(8,86,265),(105,98,340),(211,90,240),(312,115,380),(440,77,280),(528,108,325)]:
    d.rectangle((x,400-h,x+w,410),fill=(66+x//10,76+x//12,84+x//14))
    for yy in range(420-h,390,25):
        for xx in range(x+12,x+w-8,20):d.rectangle((xx,yy,xx+9,yy+12),fill=(218,216,170))
d.rectangle((0,415,640,480),fill=(48,50,54)); d.line((0,449,640,449),fill=(229,213,120),width=4)
im.save(root/'landscapes'/'skyline.jpg',quality=94)
print(root)
