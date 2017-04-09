# SiShelf

![SiShelf](/images/01.png)

Softimageのシェルフをリスペクトして作成されたMaya用のシェルフツールです。  
見た目のカスタマイズや自由な配置が行え、標準のシェルフツールよりも自分好みのシェルフを作成出来ます。  
また、Mayaメインウインドウにドッキングした状態だけでなく、フローティングウインドウとしても利用できます。  

## 準備

+ ダウロードしたSiShelfフォルダをスクリプトフォルダ（C:\Users\ユーザー名\Documents\maya\バージョン\ja_JP\scripts）に入れる。
+ SiShelf/_userSetup.py の内容を C:\Users\ユーザー名\Documents\maya\バージョン\ja_JP\scripts\userSetup.py 等の中に追記  
  ※userSetup.pyが無ければ_userSetup.pyをリネームして配置  
  ※上記パスは環境により異なる場合があります。  

## 実行

   import SiShelf.shelf  
   SiShelf.shelf.main()  
  
上記コードをスクリプトエディタ(Pythonタブ)に貼り付けて実行。  
  
  
   import SiShelf.shelf  
   SiShelf.shelf.popup()  
  
とすると、マウスの位置にポップアップします。  
ホットキーに登録して利用すると良いでしょう。

## 使い方

### Mayaウインドウへのドッキング

SiShelfはMayaのウインドウにドッキングすることができます。  
ドッキングした状態でMayaを終了すると状態が保存され、次回ドッキングした状態でMayaが起動します。  

![SiShelf](/images/04.png)

### ボタンの登録

シェルフにツールを登録する方法は以下の２つです。

+ テキストを選択してシェルフにドラッグ＆ドロップ
+ ファイルをシェルフにドラッグ＆ドロップ（.melファイル、.pyファイルに対応）

![SiShelf](/images/02.png)

ボタンの設定ウインドウが表示されるので任意の情報を入力してOKを押すとボタンが作成されます。 

![SiShelf](/images/03.gif)
  
マウスの左クリックでスクリプトを実行できます。


### 仕切り線

タブ内の整理用に仕切り線を追加できます。
縦横やラベルの有無、色などが自由に設定できます。

![SiShelf](/images/05.gif)


### タブ

マウス右クリックのコンテキストメニューからタブの追加、削除、リネームが行えます。  
タブの順番はドラッグすることで入れ替えることが可能です。  

![SiShelf](/images/06.gif)

### 操作

パーツはマウス中ドラッグで配置移動を行うことができます。

![SiShelf](/images/07.gif)

マウスの左ドラッグでシェルフに登録したパーツを矩形選択できます。
複数選択した状態でマウス中ボタンドラッグで一括移動、コンテキストメニューから削除等が出来ます。  
※現状複数選択に対応していないコマンドもあります。

![SiShelf](/images/08.gif)

### コンテキストメニュー

マウス右クリックでコンテキストメニューを表示できます。

+ Add button  
　→ ボタンを追加します。
+ Add partition  
　→ 仕切り線を追加します。
+ Edit  
　→ 選択しているパーツの内容を編集します。（複数選択には対応していません。）
+ Delete  
　→ 選択しているパーツを削除します。
+ Copy  
　→ 選択しているパーツをコピーします。（複数選択には対応していません。）
+ Paste  
　→ コピーしたパーツをクリックした位置に貼り付けます。
+ Cut  
　→ 選択しているパーツを切り取ります。（複数選択には対応していません。）
+ Tab > Add 
　→ タブを追加します。
+ Tab > Rename
　→ 現在のタブの名前を変更します。
+ Tab > Delete  
　→ 現在のタブを削除します。タブを削除するとタブに配置していたパーツ情報もすべて削除されます。
+ Default setting > Button  
　→ ボタンを作る際の初期設定を行います。
+ Default setting > Partition
　→ 仕切り線を作る際の初期設定を行います。

### データの保存

シェルフ内のデータはパーツの追加、削除、移動などの操作を行ったタイミングで自動的に保存されます。  
現状は元に戻す機能はありません。注意してください。  

データはツールと同階層のdataフォルダにjsonファイルとして作成れます。  
jsonファイルはテキストファイルなので、やろうと思えば内容を変更して保存することで手動での書き換えも可能です。  



## 動作確認

動作確認はMAYA2015でのみ行っています。  
[Qt.py](https://github.com/mottosso/Qt.py)を利用することでPySide2への行っているつもりなので、多分2016以降でも使えます。



## 改訂履歴

2017/4/9 バージョン1.0公開


## ライセンス

[MIT](https://github.com/mochio326/SiShelf/blob/master/LICENSE)