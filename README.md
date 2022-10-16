# ndldc

国立国会図書館デジタルコレクション / National Diet Library Digital Collectionから資料の画像をダウンロードします。

## 注意

本ソフトウェアは、個人向けデジタル化資料送信サービス（個人送信）でのみ公開されている資料をダウンロードする目的で開発されたものです。
個人送信を利用しなくても閲覧できる通常の資料については、IIIFマニフェストURIを利用した方が高速にダウンロードできます。

例えば、`http://dl.ndl.go.jp/info:ndljp/pid/922693`の資料に対するIIIFマニフェストURIは`https://www.dl.ndl.go.jp/api/iiif/922693/manifest.json`になります。
IIIFマニフェストURIにアクセスすることで得られるJSONファイルの`sequences`以下に、資料の各ページの画像のURIが記載されています。
これを利用して簡単なスクリプトを書けば、本ソフトウェアを利用するよりも高速にダウンロードできます。

個人送信でのみ公開されている資料についてはIIIFマニフェストURIが公開されていないため、資料のダウンロードには本ソフトウェアなどを利用する必要があります。

## 使い方

1. 個人送信に登録します。
登録方法については[こちらのページ](https://www.ndl.go.jp/jp/use/digital_transmission/individuals_index.html)を参照してください。
（ちなみに、手続きはすべてオンラインで行うことができ、申請から登録完了まで数日かかります。）

1. Poetryをインストールします。
インストール方法については[こちらのページ](https://python-poetry.org/docs/#installation)を参照してください。

1. 本リポジトリをcloneします。
    ```bash
    git clone git@github.com:ishioka0222/ndldc.git
    ```

1. 依存パッケージをインストールします。
    ```bash
    cd ndldc
    poetry install --no-dev
    ```

1. 本ソフトウェアの`download`サブコマンドを実行します。
    引数には、ダウンロードしたい資料のURLを指定します。
    ユーザー名とパスワードは、個人送信に登録した際に入力したものを指定します。
    ```bash
    poetry run ndldc download --username ユーザー名 --password パスワード https://dl.ndl.go.jp/info:ndljp/pid/1371110
    ```

## ライセンス

[LICENSE.txt](LICENSE.txt)を参照してください。

## 連絡先

<dl>
    <dt>メールアドレス</dt>
    <dd>ishioka0222 at gmail.com</dd>
</dl>
