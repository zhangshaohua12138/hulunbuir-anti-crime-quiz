from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import shutil

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "static" / "prototype"
SHOTS = SRC / "screens"
OUT = ROOT / "prototype"
(OUT / "screens").mkdir(parents=True, exist_ok=True)

SCREENS = [
    ("01-home", "活动首页", "活动主题、剩余机会、累计积分、达标线与开始答题入口；一屏看懂怎么参与。"),
    ("02-rules", "活动规则", "题型分值、每题 2 分钟、80 分达标、复活规则、六类奖品与话费奖励三档。"),
    ("03-quiz", "答题页 · 单选", "单选每题 8 分，选项整行可点；右上角显示本题倒计时。"),
    ("04-quiz-multi", "答题页 · 多选", "多选全部选对才得 12 分；漏选、多选、错选均为 0 分。"),
    ("05-result", "结果页 · 达标", "84 分示例，展示单选/多选答对构成、抽奖入口与下一步提示。"),
    ("06-result", "结果页 · 未达标", "76 分算例说明“答对 8 题不一定达标”，并提供当日复活入口。"),
    ("07-lottery", "抽奖页", "六格转盘抽奖；积分奖品直接入账，现金红包进入发放流程。"),
    ("08-ranking", "排行榜", "前 100 名、本人排名、脱敏昵称；按单套最高分（80 分以上）加抽奖积分排名，多套不累计。"),
    ("09-awards", "我的奖品", "区分现金红包、已入账积分与话费奖励，并提示手机号仅用于话费发放。"),
    ("10-modal-screen", "话费领取手机号", "活动结束后填写手机号，统一发放话费；手机号仅用于本次奖励发放。"),
]

FONT_REG = r"C:\Windows\Fonts\msyh.ttc"
FONT_BOLD = r"C:\Windows\Fonts\msyhbd.ttc"
FONT_SERIF = r"C:\Windows\Fonts\georgia.ttf"

def font(path, size):
    return ImageFont.truetype(path, size)

def wrap(draw, text, fnt, max_width):
    lines, line = [], ""
    for ch in text:
        test = line + ch
        if draw.textlength(test, font=fnt) <= max_width:
            line = test
        else:
            lines.append(line)
            line = ch
    if line:
        lines.append(line)
    return lines

def phone_image(path, target_h=1320, radius=30):
    im = Image.open(path).convert("RGB")
    ratio = target_h / im.height
    im = im.resize((round(im.width * ratio), target_h), Image.LANCZOS)
    mask = Image.new("L", im.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, im.width - 1, im.height - 1], radius, fill=255)
    rounded = Image.new("RGB", im.size, "white")
    rounded.paste(im, (0, 0), mask)
    return rounded, mask

def compose_page(title, desc, image_path, index, total=10):
    W, H = 1240, 1754
    page = Image.new("RGB", (W, H), "#f3f7fc")
    d = ImageDraw.Draw(page)
    # left accent and header
    d.rectangle([0, 0, 14, H], fill="#A9C2EA")
    d.rectangle([70, 46, 92, 92], fill="#A9C2EA")
    d.text((108, 48), "呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动", font=font(FONT_BOLD, 22), fill="#5d6f86")
    d.text((108, 78), "移动端活动页面原型", font=font(FONT_REG, 20), fill="#7a8ca3")
    d.text((W - 180, 50), f"{index:02d}", font=font(FONT_SERIF, 54), fill="#c9a45c")
    d.text((W - 120, 70), f"/ {total:02d}", font=font(FONT_REG, 18), fill="#7a8ca3")

    d.text((70, 128), title, font=font(FONT_BOLD, 43), fill="#12233c")
    y = 188
    for line in wrap(d, desc, font(FONT_REG, 21), 1090):
        d.text((70, y), line, font=font(FONT_REG, 21), fill="#6f6660")
        y += 32
    d.line([70, max(y + 12, 238), W - 70, max(y + 12, 238)], fill="#dbe5f0", width=2)

    phone, mask = phone_image(image_path, target_h=1318)
    x = (W - phone.width) // 2
    y0 = max(y + 28, 252)
    # shadow
    shadow = Image.new("RGBA", phone.size, (0, 0, 0, 0))
    ImageDraw.Draw(shadow).rounded_rectangle([0, 0, phone.width - 1, phone.height - 1], 30, fill=(54, 31, 18, 70))
    shadow = shadow.filter(ImageFilter.GaussianBlur(22))
    page.paste(shadow, (x + 10, y0 + 16), shadow)
    page.paste(phone, (x, y0), mask)
    d.rounded_rectangle([x - 1, y0 - 1, x + phone.width, y0 + phone.height], 31, outline="#cfddec", width=2)

    d.text((70, H - 66), "说明：页面数据、昵称与订单号为原型示意；正式题库、奖品档位及活动时间以主办方最终确认为准。", font=font(FONT_REG, 16), fill="#7a8ca3")
    return page

# cover
W, H = 1240, 1754
cover = Image.new("RGB", (W, H), "#f3f7fc")
d = ImageDraw.Draw(cover)
d.rectangle([0, 0, W, 500], fill="#A9C2EA")
d.rectangle([0, 500, W, 508], fill="#c9a45c")
# decorative circles / shield-ish
d.ellipse([900, 10, 1420, 530], outline="#c9a45c", width=2)
d.ellipse([980, 90, 1340, 450], outline="#c9a45c", width=1)
d.polygon([(1070, 120), (1220, 175), (1220, 300), (1070, 390), (920, 300), (920, 175)], outline="#e4bd82", width=3)
d.text((86, 80), "HULUNBUIR · PEACE & JUSTICE", font=font(FONT_REG, 20), fill="#1d477c")
d.text((80, 128), "呼伦贝尔市深化扫黑除恶专项斗争", font=font(FONT_BOLD, 46), fill="#0b2b55")
d.text((80, 194), "有奖答题活动", font=font(FONT_BOLD, 60), fill="#123a66")
d.text((84, 300), "移动端活动页面原型", font=font(FONT_REG, 34), fill="#1d477c")
d.text((84, 356), "活动首页 / 规则 / 答题 / 结果 / 抽奖 / 排行榜 / 领奖", font=font(FONT_REG, 20), fill="#2b4f7d")
d.text((84, 398), "共 10 屏 · 适配 320–430px 手机宽度", font=font(FONT_REG, 20), fill="#2b4f7d")

d.text((80, 570), "原型说明", font=font(FONT_BOLD, 26), fill="#2F5D9A")
para = "本原型用于客户评审与活动方案确认，展示移动端页面的信息层级、核心交互与视觉风格。页面内积分、昵称、订单号均为示意数据；正式题库、奖品档位、活动时间和主办文案以最终确认版本为准。"
y = 616
for line in wrap(d, para, font(FONT_REG, 20), 1050):
    d.text((80, y), line, font=font(FONT_REG, 20), fill="#3f536b")
    y += 34

d.text((80, 780), "页面清单", font=font(FONT_BOLD, 26), fill="#2F5D9A")
col_x = [80, 660]
for i, (_, title, _) in enumerate(SCREENS):
    col = 0 if i < 5 else 1
    row = i if i < 5 else i - 5
    x = col_x[col]
    yy = 840 + row * 62
    d.text((x, yy), f"{i + 1:02d}", font=font(FONT_SERIF, 24), fill="#c9a45c")
    d.text((x + 52, yy + 4), title, font=font(FONT_REG, 21), fill="#1b3350")

d.text((80, 1180), "活动信息", font=font(FONT_BOLD, 26), fill="#A9C2EA")
d.text((80, 1225), "活动名称：呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动", font=font(FONT_REG, 19), fill="#3f536b")
d.text((80, 1262), "主办单位：中共呼伦贝尔市委政法委员会", font=font(FONT_REG, 19), fill="#3f536b")
d.text((80, 1299), "活动时间：2026 年 11 月 13 日 — 11 月 20 日", font=font(FONT_REG, 19), fill="#3f536b")
d.text((80, 1336), "活动规则：每套 10 题，单选 8 分、多选 12 分；每题 2 分钟；80 分达标可抽奖。", font=font(FONT_REG, 19), fill="#3f536b")

d.rectangle([80, 1430, W - 80, 1432], fill="#ddd2c2")
d.text((80, 1470), "视觉方向：政法红 + 暖白 + 金色，强调权威、温暖、可参与。", font=font(FONT_REG, 18), fill="#7a8ca3")
d.text((80, 1504), "适配方向：触控目标不小于 40px，输入框 16px 防 iOS 放大，底部导航预留安全区。", font=font(FONT_REG, 18), fill="#7a8ca3")
d.text((80, 1640), "呼伦贝尔市骏驰文化传媒有限公司 · 原型稿 V1.0", font=font(FONT_REG, 17), fill="#7a8ca3")
cover.save(OUT / "cover.png")

pages = [cover]
for i, (name, title, desc) in enumerate(SCREENS, start=1):
    path = SHOTS / f"{name}.png"
    pages.append(compose_page(title, desc, path, i))
    shutil.copyfile(path, OUT / "screens" / f"{name}.png")

pages[0].save(OUT / "活动页面原型.pdf", "PDF", resolution=150.0, save_all=True, append_images=pages[1:])

# overview contact sheet
thumb_w, thumb_h = 300, 650
cols, rows = 5, 2
pad_x, pad_top, gap = 60, 170, 34
canvas_w = cols * thumb_w + (cols - 1) * gap + pad_x * 2
canvas_h = pad_top + rows * (thumb_h + 52) + (rows - 1) * 20 + 80
sheet = Image.new("RGB", (canvas_w, canvas_h), "#f3f7fc")
sd = ImageDraw.Draw(sheet)
sd.rectangle([0, 0, canvas_w, 10], fill="#A9C2EA")
sd.text((pad_x, 42), "呼伦贝尔市深化扫黑除恶专项斗争有奖答题活动", font=font(FONT_BOLD, 30), fill="#12233c")
sd.text((pad_x, 84), "移动端活动页面原型 · 10 屏总览", font=font(FONT_REG, 20), fill="#8b8178")
sd.text((canvas_w - 310, 50), "原型示意 · 客户评审", font=font(FONT_REG, 16), fill="#b09a76")
for i, (name, title, _) in enumerate(SCREENS):
    r, c = divmod(i, cols)
    im = Image.open(SHOTS / f"{name}.png").convert("RGB").resize((thumb_w, thumb_h), Image.LANCZOS)
    mask = Image.new("L", (thumb_w, thumb_h), 0)
    ImageDraw.Draw(mask).rounded_rectangle([0, 0, thumb_w - 1, thumb_h - 1], 14, fill=255)
    x = pad_x + c * (thumb_w + gap)
    y = pad_top + r * (thumb_h + 72)
    sd.rounded_rectangle([x + 4, y + 8, x + thumb_w + 4, y + thumb_h + 8], 15, fill="#dce7f4")
    sheet.paste(im, (x, y), mask)
    sd.rectangle([x, y + thumb_h + 4, x + 4, y + thumb_h + 20], fill="#A9C2EA")
    sd.text((x + 12, y + thumb_h + 8), f"{i + 1:02d}  {title}", font=font(FONT_REG, 17), fill="#4b423d")
sd.text((pad_x, canvas_h - 48), "说明：页面内数据为示意；正式题库、奖品档位与活动时间以主办方最终确认为准。", font=font(FONT_REG, 15), fill="#7a8ca3")
sheet.save(OUT / "活动页面原型-总览.png")

# board for browser viewing
shutil.copyfile(SRC / "board.html", OUT / "index.html")
print("PDF pages:", len(pages))
print("PDF:", OUT / "活动页面原型.pdf", (OUT / "活动页面原型.pdf").stat().st_size)
print("Overview:", OUT / "活动页面原型-总览.png", (OUT / "活动页面原型-总览.png").stat().st_size)
