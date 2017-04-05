# SiShelf（説明仮）


Softimageのシェルフをリスペクトして作成されたMaya用のシェルフツールです。
ボタンの見た目のカスタマイズなどが行え、標準のシェルフツールよりも自分好みのシェルフを作成出来ます。
また、Mayaメインウインドウにドッキングした状態だけでなく、フローティングウインドウとしても利用できます。

## 事前準備

+ ダウロードしたSiShelfフォルダをスクリプトフォルダ（C:\Users\ユーザー名\Documents\maya\バージョン\ja_JP\scripts）に入れる。
+ SiShelf/_userSetup.py の内容を C:\Users\ユーザー名\Documents\maya\バージョン\ja_JP\scripts\userSetup.py の中に追記
  userSetup.pyが無ければ_userSetup.pyをリネームして配置

## 実行方法

import SiShelf.shelf
SiShelf.shelf.main()

上記コードをスクリプトエディタ(Pythonタブ)に貼り付けて実行。


import SiShelf.shelf
SiShelf.shelf.popup()

とすると、マウスの位置にポップアップします。


## 使い方


### ボタンの登録

ウインドウにテキストを選択、もしくはファイルをドラッグ＆ドロップします。
ボタンの設定ウインドウが表示されるので任意の情報を入力してOKを押すとボタンが作成されます。

ボタンはマウスの左クリックで実行、中ボタンのドラッグ＆ドロップで移動が出来ます。


## その他


## 動作確認

動作確認はMAYA2015でのみ行っています。

## 改訂履歴
