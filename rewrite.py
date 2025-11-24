def naosu(input, output):
    """
    指定されたファイルの内容を別のファイルに上書きする関数
    """
    source_file = input
    destination_file = output

    try:
        # ファイルの内容を読み取り、別のファイルに書き込む
        with open(source_file, 'r', encoding='utf-8') as src:
            content = src.read()

        with open(destination_file, 'w', encoding='utf-8') as dst:
            dst.write(content)

        print(f"'{source_file}' の内容を '{destination_file}' に書き直しました！")

    except FileNotFoundError:
        print(f"エラー: ファイル '{source_file}' が見つかりません。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

# このブロック内のコードは、rewrite.pyが直接実行された時だけ動作します。
if __name__ == "__main__":
    # ここにテスト用のコードを追加します。
    # 例:
    # with open("test_source.txt", "w", encoding="utf-8") as f:
    #     f.write("これはテスト内容です。\n")
    # naosu("test_source.txt", "test_destination.txt")
    print("rewrite.pyが直接実行されました。")