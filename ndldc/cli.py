from Crypto.Cipher import AES
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from PIL import Image
import base64
import click
import io
import json
import os
import random
import re
import requests
import time
import urllib


@click.group()
def cli():
    # メインの処理は各コマンドで行う
    pass


@cli.command()
@click.argument('url')
@click.option('--username', required=True)
@click.option('--password', required=True)
def download(url, username, password):
    # URLからpidを取得する
    url_pattern = r"https://dl.ndl.go.jp/pid/(\d+)/.*"
    match = re.match(url_pattern, url)
    if match is None:
        raise Exception("invalid url")
    pid = match.group(1)

    # ピース情報取得のためのPEM形式の公開鍵と秘密鍵を生成する
    rsa_key_pair = RSA.generate(1024)
    public_key_string = rsa_key_pair.publickey().exportKey().decode()

    # セッションを作成する
    session = requests.Session()

    # ログインする
    login_url = "https://dl.ndl.go.jp/api/auth/sso/login"
    payload = {
        "cardId": username,
        "password": password,
    }
    response = session.post(url=login_url, json=payload)
    if response.status_code != 200:
        raise Exception("login failed")

    # メタデータを取得する
    search_url = f"https://dl.ndl.go.jp/api/item/search/info:ndljp/pid/{pid}"
    response = session.get(url=search_url)
    if response.status_code != 200:
        raise Exception("search request failed")
    search_data = response.json()

    # ファイル格納用のディレクトリを作成する
    title = search_data["item"]["meta"]["0001Dtct"][0]
    volume = search_data["item"]["meta"]["0007Dtct"][0]
    dirname = f"{title}_{volume}"
    if not os.path.exists(dirname):
        os.mkdir(dirname)

    # トークンを取得する
    token_url = f"https://dl.ndl.go.jp/api/restriction/issue/token/info:ndljp/pid/{pid}"
    response = session.get(url=token_url)
    if response.status_code != 200:
        raise Exception("token request failed")
    token_data = response.json()
    timestamp = token_data["timestamp"]
    tokens = token_data["tokens"]

    for contents_bundle in search_data["item"]["contentsBundles"]:
        bid = contents_bundle["id"]
        contents = contents_bundle["contents"]
        for koma_index, koma in enumerate(contents):
            # 進捗を表示する
            padded_content_index = str(koma_index+1).zfill(4)
            print(f"\t{padded_content_index}枚目のコマを取得中...")

            # コマ画像のファイル名を決定する
            original_filename = koma["originalFileName"]
            if not original_filename.endswith(".jp2"):
                raise Exception("invalid file format")
            filename = original_filename.replace(".jp2", ".jpg")
            filepath = os.path.join(dirname, filename)

            # 既にコマ画像が存在する場合はスキップする
            if (os.path.exists(filepath)):
                print(f"\t{padded_content_index}枚目のコマは既に存在します")
                continue

            # コマ情報を取得する
            cid = koma["id"]
            komainfo_url = f"https://dl.ndl.go.jp/contents/{pid}/{bid}/{cid}/komainfo.json"
            response = session.get(url=komainfo_url)
            if response.status_code != 200:
                raise Exception("komainfo request failed")
            komainfo = response.json()

            # タイル情報のうち、画像サイズが最大のものを保持する
            levels = komainfo["Levels"]
            level = max(
                levels, key=lambda level: level["OriginWidth"] * level["OriginHeight"])

            # タイル情報を保持する
            tiles = level["Tiles"]
            cols = level["TileX"]
            rows = level["TileY"]
            tile_size = level["TileSize"]
            piece_size = tile_size // 4

            # ピース情報を取得する
            deobfucsate_url = f"https://dl.ndl.go.jp/apigw-ex/info/deobfuscate"
            payload = {
                "objectKey": f"{pid}_{bid}_{cid}",
                "pubKeyPem": public_key_string
            }
            response = session.post(url=deobfucsate_url, json=payload)
            encrypted_tile_info = response.text
            decryptor = PKCS1_v1_5.new(rsa_key_pair)
            sentinel = get_random_bytes(16)
            decrypted_tile_info = decryptor.decrypt(
                base64.b64decode(encrypted_tile_info), sentinel).decode()
            piece_mapping = list(map(int, decrypted_tile_info.split(",")))

            # コマ画像を作成する
            koma_width = level["OriginWidth"]
            koma_height = level["OriginHeight"]
            koma_image = Image.new("RGB", (koma_width, koma_height))

            # 各タイルを取得してkoma_imageに貼り付ける
            for tile_index, tile_image in enumerate(tiles):
                # タイル画像のダウンロードを1秒間隔で行う
                # NOTE: あまり頻繁にアクセスを行わないように注意する
                time.sleep(1)

                # 進捗を表示する
                padded_tile_index = str(tile_index+1).zfill(4)
                print(f"\t\t{padded_tile_index}枚目のタイルを取得中...")

                tile_url = urllib.parse.urljoin(
                    f"https://dl.ndl.go.jp/contents/{pid}/{bid}/{cid}/", tile_image)

                # ランダムな4桁の数字からなるIDを生成する
                # NOTE: このIDが実際には何を表しているのかは不明
                digits = 4
                id_ = random.randrange(10**(digits-1), 10**digits)
                # tokenを生成する
                data = {
                    "cid": cid,
                    "token": tokens[cid],
                    "timestamp": timestamp,
                    "id": id_
                }

                # paramsを生成する
                # NOTE: json.dumps()で生成した文字列にスペースが含まれると、
                # リクエストが失敗するので、separatorsオプションを指定する
                payload = {
                    "token": json.dumps(data, separators=(',', ':'))
                }

                # タイルを取得する
                response = session.get(url=tile_url, params=payload)
                if response.status_code != 200:
                    raise Exception("tile request failed")
                tile_data = response.content

                # タイルに含まれるピースを並べ替える
                tile_image = Image.open(io.BytesIO(tile_data))
                unpuzzled_tile_image = Image.new(
                    "RGB", (tile_size, tile_size))

                actual_tile_size = tile_image.size[0]
                actual_piece_size = actual_tile_size // 4
                padding_size = (actual_piece_size - piece_size) // 2
                for src_piece_index, dest_piece_index in enumerate(piece_mapping):
                    src_x = (src_piece_index % 4) * \
                        actual_piece_size + padding_size
                    src_y = (src_piece_index // 4) * \
                        actual_piece_size + padding_size
                    src_rect = (
                        src_x,
                        src_y,
                        src_x + piece_size,
                        src_y + piece_size
                    )
                    dest_x = (dest_piece_index % 4) * piece_size
                    dest_y = (dest_piece_index // 4) * piece_size

                    piece = tile_image.crop(src_rect)
                    unpuzzled_tile_image.paste(piece, (dest_x, dest_y))

                # 並べ替えたタイルをコマ画像に貼り付ける
                col = tile_index % cols
                row = tile_index // cols
                x = col * tile_size
                y = row * tile_size
                koma_image.paste(unpuzzled_tile_image, (x, y))

            # コマ画像を保存する
            koma_image.save(filepath)


def main():
    cli()


if __name__ == '__main__':
    main()
