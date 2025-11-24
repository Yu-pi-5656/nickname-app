def kakikomi(input, output):
    """
    指定されたファイルの内容を別のファイルに追加で書き込む関数
    """
    source_file = input
    destination_file = output

    try:
        # ファイルの内容を読み取り、別のファイルに書き込む
        with open(source_file, 'r', encoding='utf-8') as src:
            content = src.read()

        with open(destination_file, 'a', encoding='utf-8') as dst:
            dst.write(content)
        
        print(f"'{source_file}' の内容を '{destination_file}' に追加で書き込みました。")
        
    except FileNotFoundError:
        print(f"エラー: ファイル '{source_file}' が見つかりません。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# このブロック内のコードは、postscript.pyが直接実行された時だけ動作します。
if __name__ == "__main__":
    # 以下はテスト用のコード
    # 実際のファイルパスに置き換えて使用してください。
    # 例:
    # with open("test_source.txt", "w", encoding="utf-8") as f:
    #     f.write("これはテスト内容です。\n")
    # kakikomi("test_source.txt", "test_destination.txt")
    print("postscript.pyが直接実行されました。")