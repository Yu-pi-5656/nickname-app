import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig # BitsAndBytesConfigをインポート
import gc 

model = None
tokenizer = None
model_name = "Qwen/Qwen3-8B"

def niku(out):
    global model, tokenizer

    if model is None:
        torch.cuda.empty_cache()
        gc.collect()

        # BitsAndBytesConfigを使用して、引数を統一する
        # load_in_4bit などの非推奨引数は削除
        bnb_config = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type="nf4",
            bnb_4bit_compute_dtype=torch.float32, # 数値安定のため
        )

        tokenizer = AutoTokenizer.from_pretrained(model_name)
        
        try:
            model = AutoModelForCausalLM.from_pretrained(
                model_name,
                quantization_config=bnb_config, # <-- これを使用する
                device_map="auto",
                low_cpu_mem_usage=True, # <-- モデルロードの引数はこれだけに絞る
            )
            print("Qwen3モデルのロードが完了しました。")
        except Exception as e:
            print(f"Qwen3モデルロード中にエラーが発生しました: {e}")
            raise e
    
    messages = [
        {"role": "user", "content": out}
    ]
    text = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True,
        enable_thinking=False
    )
    
    model_inputs = tokenizer([text], return_tensors="pt")
    device = next(model.parameters()).device
    model_inputs = {k: v.to(device) for k, v in model_inputs.items()}
    
    model.eval()
    with torch.inference_mode():
        generated_ids = model.generate(
            **model_inputs,
            max_new_tokens=1512,
            do_sample=True,     # greedyは禁止
            temperature=0.6,
            top_p=0.95,
            top_k=20,
            min_p=0,
            pad_token_id=tokenizer.eos_token_id,
            eos_token_id=tokenizer.eos_token_id,
        )
    
    output_ids = generated_ids[0][len(model_inputs["input_ids"][0]):].tolist()
    # ... (パース処理はそのまま)
    
    try:
        index = len(output_ids) - output_ids[::-1].index(151668)
    except ValueError:
        index = 0

    thinking_content = tokenizer.decode(output_ids[:index], skip_special_tokens=True).strip("\n")
    content = tokenizer.decode(output_ids[index:], skip_special_tokens=True).strip("\n")

    return content