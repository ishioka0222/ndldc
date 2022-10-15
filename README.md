# ndldc

## 概要

国立国会図書館デジタルコレクション / National Diet Library Digital Collectionから画像をダウンロードします。

## 使い方

```bash
git clone git@github.com:ishioka0222/ndldc.git
cd ndldc
poetry install --no-dev
poetry run ndldc download --username ユーザー名 --password パスワード https://dl.ndl.go.jp/info:ndljp/pid/1383303
```
