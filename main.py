from flask import Flask, render_template, request, send_from_directory
import os
from PIL import Image, ExifTags

# ← あなたのロジックをインポート
import rewrite
import qwen25
import postscript
import qwen3

def fix_image_orientation(image_path):
    try:
        img = Image.open(image_path)

        exif = img._getexif()
        if exif is None:
            return

        # Orientation タグの番号を取得
        for orientation in ExifTags.TAGS.keys():
            if ExifTags.TAGS[orientation] == "Orientation":
                break

        orientation_value = exif.get(orientation, None)

        # 必要に応じて回転
        if orientation_value == 3:
            img = img.rotate(180, expand=True)
        elif orientation_value == 6:
            img = img.rotate(270, expand=True)
        elif orientation_value == 8:
            img = img.rotate(90, expand=True)

        img.save(image_path)
        img.close()

    except Exception as e:
        print("EXIF orientation fix error:", e)

# ============================
# Flask アプリ
# ============================
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)


# ============================
# ロジック：generate_nickname
# ============================
def generate_nickname(image_path: str, name: str, furigana: str, extra_info: str = "") -> dict:
    os.makedirs("output", exist_ok=True)
    os.makedirs("end", exist_ok=True)
    os.makedirs("example", exist_ok=True)

    with open("prompt/vlm.txt", "r", encoding="utf-8") as f:
        out = f.read()

    base = os.path.splitext(os.path.basename(image_path))[0]

    output_file = f"output/output_{base}.txt"
    exam_file = f"example/example_{base}.txt"
    end_file = f"end/end_{base}.txt"

    # 特徴生成
    feature = qwen25.tokutyou(image_path, out)
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(feature.replace('\n', ' '))

    # プロンプト加工
    rewrite.naosu("prompt/puro base.txt", "prompt/puro.txt")
    rewrite.naosu("prompt/features base.txt", "prompt/features.txt")
    rewrite.naosu("prompt/example base.txt", "prompt/example.txt")
    rewrite.naosu("prompt/name base.txt", "prompt/name.txt")
    postscript.kakikomi(output_file, "prompt/features.txt")

    with open("prompt/name.txt", "a", encoding="utf-8") as f:
        f.write(f"\t名前: {name}\tふりがな: {furigana}\t自由記入: {extra_info}\n")

    postscript.kakikomi("prompt/name.txt", "prompt/features.txt")
    postscript.kakikomi("prompt/features.txt", "prompt/puro.txt")
    postscript.kakikomi("prompt/features.txt", "prompt/example.txt")

    # 例え生成
    with open("prompt/example.txt", "r", encoding="utf-8") as f2:
        exam = f2.read()
    example = qwen3.niku(exam)

    with open(exam_file, "w", encoding="utf-8") as f3:
        f3.write(example.replace('\n', ' '))

    postscript.kakikomi("prompt/examfront.txt", "prompt/puro.txt")
    postscript.kakikomi(exam_file, "prompt/puro.txt")
    postscript.kakikomi("prompt/puro back.txt", "prompt/puro.txt")

    # 整形
    with open("prompt/puro.txt", "r", encoding="utf-8") as f_read:
        current_puro = f_read.read()
    with open("prompt/puro.txt", "w", encoding="utf-8") as f4:
        f4.write(current_puro.replace('\n', ' '))

    # ニックネーム生成
    with open("prompt/puro.txt", "r", encoding="utf-8") as f5:
        puro = f5.read()
    nickname = qwen3.niku(puro)

    with open(end_file, "w", encoding="utf-8") as f6:
        f6.write(nickname)

    return {
        "nickname": nickname,
        "feature": feature,
        "example": example
    }


# ============================
# 画像サーブ（Flask 用）
# ============================
@app.route("/uploads/<path:filename>")
def serve_image(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# ============================
# メイン画面
# ============================
@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        image = request.files["image"]
        name = request.form["name"]
        furigana = request.form["furigana"]
        extra_info = request.form.get("extra_info", "")

        img_filename = image.filename
        img_path = os.path.join(app.config['UPLOAD_FOLDER'], img_filename)

        img = Image.open(image)
        img = img.convert("RGB")
        img.thumbnail((400, 400))
        img.save(img_path)

        fix_image_orientation(img_path)

        result = generate_nickname(img_path, name, furigana, extra_info)

        return render_template("result.html",
                               nickname=result["nickname"],
                               feature=result["feature"],
                               example=result["example"],
                               img_path=img_filename)

    return render_template("index.html")


# ============================
# Render 用エントリポイント
# ============================
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
