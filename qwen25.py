import torch
import gc
from transformers import Qwen2_5_VLForConditionalGeneration, AutoProcessor, BitsAndBytesConfig
from qwen_vl_utils import process_vision_info
import os
from PIL import Image

model = None
processor = None
MODEL_NAME = "Qwen/Qwen2.5-VL-7B-Instruct"

max_memory = {
    0: "8GiB",   # GPU 0 に 8GB 割り当て
    1: "8GiB",   # GPU 1 に 8GB 割り当て
    "cpu": "16GiB", # CPU (RAM) に 16GB 割り当ててオフロードを許可
}

# --- 画像リサイズ関数 ---
def resize_image(image_path, max_size=1024):
    """
    画像を長辺 max_size ピクセル以内に収めてリサイズ。
    RGB変換も行う。
    """
    try:
        img = Image.open(image_path).convert("RGB")
        img.thumbnail((max_size, max_size))
        return img
    except Exception as e:
        print(f"画像のリサイズに失敗しました: {e}")
        raise

def tokutyou(syasin, out):
    global model, processor

    # --- モデル初期化 ---
    if model is None:
        torch.cuda.empty_cache()
        gc.collect()

        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float32,
        )

        offload_dir = os.path.join(os.path.dirname(__file__), "offload_qwen25")
        os.makedirs(offload_dir, exist_ok=True)

        print(f"[{MODEL_NAME}] モデルをロード中...")

        try:
            model = Qwen2_5_VLForConditionalGeneration.from_pretrained(
                MODEL_NAME,
                quantization_config=bnb_config,
                device_map="auto",
                low_cpu_mem_usage=True,
                max_memory=max_memory,
                #offload_folder="offload",
            )
            processor = AutoProcessor.from_pretrained(MODEL_NAME)
            print("モデルのロードが完了しました。")
        except Exception as e:
            print(f"モデルロード中にエラーが発生しました: {e}")
            torch.cuda.empty_cache()
            gc.collect()
            raise e

    # --- 画像をリサイズして読み込み ---
    resized_image = resize_image(syasin, max_size=1024)

    # --- 推論メッセージ作成 ---
    messages = [{
        "role": "user",
        "content": [
            {"type": "image", "image": resized_image},
            {"type": "text", "text": out},
        ],
    }]

    # --- 入力データ生成 ---
    text = processor.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
    image_inputs, video_inputs = process_vision_info(messages)

    inputs = processor(
        text=[text],
        images=image_inputs,
        videos=video_inputs,
        padding=True,
        return_tensors="pt",
    )

    # --- デバイス転送 ---
    device = next(model.parameters()).device
    inputs = {k: v.to(device) for k, v in inputs.items()}

    # --- 推論実行 ---
    model.eval()
    with torch.inference_mode():
        generated_ids = model.generate(
            **inputs,
            max_new_tokens=512,
            do_sample=False,
            num_beams=1,
            pad_token_id=processor.tokenizer.eos_token_id,
            eos_token_id=processor.tokenizer.eos_token_id,
        )

    # --- 出力整形 ---
    input_len = inputs["input_ids"].shape[1]
    if generated_ids.shape[1] > input_len:
        generated_trim = generated_ids[:, input_len:]
    else:
        generated_trim = generated_ids.new_empty((generated_ids.shape[0], 0), dtype=generated_ids.dtype)

    output_text = processor.batch_decode(
        generated_trim,
        skip_special_tokens=True,
        clean_up_tokenization_spaces=True
    )[0].strip()

    return output_text
