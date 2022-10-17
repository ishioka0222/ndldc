from Crypto.Cipher import AES
from PIL import Image
import click
import io
import json
import math
import os
import time

from . Frame import Frame
from . Session import Session


@click.group()
def cli():
    pass


@cli.command()
@click.argument('url')
@click.option('--username', required=True)
@click.option('--password', required=True)
def download(url, username, password):
    # TODO: Downloaderクラスなどを作りリファクタリングする

    # create session
    session = Session()

    # login
    session.login(username, password)

    # fetch frame to get book metadata
    html = session.get(url=url)
    frame = Frame.from_html(html)

    # store content metadata
    frame_count = frame.get_last_content_no()
    content_root_url = frame.metadata["identifier:URI"]
    num_of_digits = len(str(frame_count))

    # create directory
    # TODO: volumeが存在しない場合を考慮する
    # TODO: titleやvolumeにファイル名に使えない文字が含まれている場合を考慮する
    title = frame.metadata["title"]
    volume = frame.metadata["volume"]
    dir_name = f"{title}_{volume}"
    if not os.path.exists(dir_name):
        os.mkdir(dir_name)

    # download
    for i in range(1, frame_count + 1):
        filename = f"{dir_name}/{i:0{num_of_digits}}.jpg"

        if os.path.exists(filename):
            print(f"skipping page {i}/{frame_count}")
            continue

        print(f"downloading page {i}/{frame_count}")

        # fetch frame
        frame_url = f"{content_root_url}/{i}"
        content = session.get(url=frame_url)
        frame = Frame.from_html(content)

        # fetch image info
        root_url = "https://dl.ndl.go.jp"
        path = frame.get_content_image_root_path()
        content_id = frame.get_content_id()
        common_params = frame.get_content_custom_param()
        info_url = f"{root_url}{path}/{content_id}"

        content = session.get(url=info_url, params=common_params)
        info = json.loads(content)

        # store metadata
        max_zoom_level = info["maxZoomLevel"]
        image_width = info["imageWidth"]
        image_height = info["imageHeight"]
        tile_width = info["tileWidth"]
        tile_height = info["tileHeight"]

        columns = math.ceil(image_width / tile_width)
        rows = math.ceil(image_height / tile_height)
        whole_size = (image_width, image_height)
        tile_size = (tile_width, tile_height)

        # prepare image
        whole_image = Image.new(mode="RGB", size=whole_size)

        # download, decrypt and paste tiles
        for row in range(rows):
            for column in range(columns):
                print(f"    downloading tile col={column}, row={row}")

                # build url
                tile_url = info_url.replace("/info/", "/tile/")
                tile_url = f"{tile_url}/{max_zoom_level}/{column}_{row}.jpg"

                # build params
                x = column * tile_width
                y = row * tile_height
                tile_params = {
                    "rotate": 0,
                    "x": x,
                    "y": y,
                    "tileWidth": tile_width,
                    "tileHeight": tile_height,
                    "extension": "jp2",
                }
                tile_params.update(common_params)

                # download
                content = session.get(url=tile_url, params=tile_params)

                # decrypt
                key = info["ck"].encode('utf-8')
                iv = key[:16]
                cipher = AES.new(key=key, mode=AES.MODE_CBC, iv=iv)
                decrypted = cipher.decrypt(content)

                # paste
                buffer = io.BytesIO(decrypted)
                tile_image = Image.open(buffer)
                whole_image.paste(tile_image, (x, y))

                time.sleep(1.5)

        # save image
        whole_image.save(filename)


def main():
    cli()


if __name__ == '__main__':
    main()
