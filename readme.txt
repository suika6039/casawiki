YukiWiki - 自由にページを追加・削除・編集できるWebページ構築CGI

-------------------------------------------------
■作者
-------------------------------------------------

Copyright (C) 2000-2006 by Hiroshi Yuki.
結城浩 <hyuki@hyuki.com>
http://www.hyuki.com/
http://www.hyuki.com/yukiwiki/


-------------------------------------------------
■最新情報
-------------------------------------------------

以下のURLで最新情報を入手してください。
http://www.hyuki.com/yukiwiki/


-------------------------------------------------
■はじめに
-------------------------------------------------

YukiWiki（結城ウィキ）は参加者が自由にページを追加・削除・編集できるという
不思議なWebページ群を作るCGIです。
Webで動作する掲示板とちょっと似ていますが、
Web掲示板が単にメッセージを追加するだけなのに対して、
YukiWikiは、Webページ全体を自由に変更することができます。

YukiWikiは、Ward CunninghamのWikiの仕様を参考にして独自に作られました。
こういったCGIは世界中に無数にあり「Wikiクローン」と呼ばれています。
YukiWikiはWikiクローンの一種です。

YukiWikiはPerlで書かれたCGIスクリプトとして実現されていますので、
Perlが動作するWebサーバならば比較的容易に設置できます。

YukiWikiはフリーソフトです。
ご自由にお使いください。


-------------------------------------------------
■ライセンス
-------------------------------------------------

This program is free software; you can redistribute it and/or
modify it under the same terms as Perl itself.

-------------------------------------------------
■設置手順
-------------------------------------------------

(1) wiki.cgiの一行目をあなたのサーバに合わせて修正します。
    例1
    #!/usr/bin/perl

    例2:WindowsのActivePerlの場合
    #!perl

(2) wiki.cgiのはじめの方にある、変数$modifier_...の値を修正します(必須)

    my $modifier_mail
        管理者メールアドレス

    my $modifier_url
        管理者Webページ

    my $modifier_name
        管理者名前

    my $modifier_dbtype
        データベースの種類(以下のいずれか)
            'YukiWikiDB'        (推奨)入力されたテキストをそのままファイルとして保存
            'dbmopen'           サーバによって使えない場合あり
            'AnyDBM_File'       サーバによって使えない場合あり

    my $modifier_sendmail
        YukiWiki書き込み時に管理者にメールを送るための
        sendmailのコマンドライン
            '/usr/sbin/sendmail -t -n'      一例
            ''                              メールを送らない/送れない場合

    my $modifier_dir_data
        CGIが読み書きするデータを置くディレクトリ。

    my $modifier_url_data
        CSSや画像ファイルを置くディレクトリに対応したURL。

    my $modifier_rss_title
        タイトル(RSS用)

    my $modifier_rss_link
        設置するYukiWikiのURL(RSS用)

    my $modifier_rss_about
        RSSフィードのURL(RSS用)

    my $modifier_rss_description
        説明文(RSS用)


(3) 「ファイル一覧」にあるファイルをサーバに転送します。
    転送モードやパーミッションを適切に設定します。

(4) ブラウザでサーバ上のwiki.cgiのURLにアクセスします。

(5) FrontPageが表示されたら、AdminChangePasswordというリンクをたどって、
    管理者用のパスワードを設定します。

(6) 設定が済んだら、frontpage.txtファイルを書き換え、再度転送します。


-------------------------------------------------
■ファイル一覧
-------------------------------------------------

●説明文

以下のファイルは、
Webサーバに転送する必要はありません。

+-- readme.txt          解説文書（このファイル）
+-- plugin.txt          プラグイン解説
+-- history.txt         開発記録


●CGI群

以下のファイルはCGIが実行できるディレクトリにFTPします。

                         転送モード  パーミッション      説明
+-- wiki.cgi             TEXT        755 (rwxr-xr-x)     CGI本体
+-- jcode.pl             TEXT        644 (rw-r--r--)     文字コード変換ライブラリ
+-- Yuki                             755 (rwxr-xr-x)     ディレクトリ
|   +-- YukiWikiDB.pm    TEXT        644 (rw-r--r--)     ファイルベースのDB用
|   +-- RSS.pm           TEXT        644 (rw-r--r--)     RSS用
|   +-- DiffText.pm      TEXT        644 (rw-r--r--)     差分用
|   +-- PluginManager.pm TEXT        644 (rw-r--r--)     プラグイン用
+-- Algorithm                        755 (rwxr-xr-x)     ディレクトリ
    +-- Diff.pm          TEXT        644 (rw-r--r--)     差分用

●プラグイン

以下のファイルは、
wiki.cgi内の変数$modifier_dir_pluginで指定するディレクトリに転送します。

+-- plugin                          755 (rwxr-xr-x)     ディレクトリ
    +-- link.pl         TEXT        644 (rw-r--r--)     linkプラグイン
    +-- recent.pl       TEXT        644 (rw-r--r--)     recentプラグイン
    +-- ruby.pl         TEXT        644 (rw-r--r--)     rubyプラグイン
    +-- verb.pl         TEXT        644 (rw-r--r--)     verbプラグイン

●参照ファイル

以下のファイルは、
wiki.cgi内の変数$modifier_dir_dataで指定するディレクトリに転送します。

                    転送モード  パーミッション      説明
+-- rss.xml         TEXT        666 (rw-rw-rw-)     RSSファイル
+-- touched.txt     TEXT        666 (rw-rw-rw-)     編集時の更新ファイル
+-- frontpage.txt   TEXT        644 (rw-r--r--)     FrontPageのテキスト
+-- resource.txt    TEXT        644 (rw-r--r--)     リソースファイル
+-- conflict.txt    TEXT        644 (rw-r--r--)     更新の衝突時のテキスト
+-- format.txt      TEXT        644 (rw-r--r--)     整形ルールのテキスト

プロバイダによっては、
CGIを置くディレクトリにあるファイルは、CGIからアクセスできない場合があります。

その場合には、変数$modifier_dir_dataを使って、
「CGIが読み書きできるファイルを置くディレクトリ」を指定しておき、
そのディレクトリに上記のファイルを転送します。

そのような制限がない場合には、
変数$modifier_dir_dataではwiki.cgiを転送したディレクトリを指定し、
同じディレクトリに上記ファイルを転送します。


●スタイルシートと画像ファイル

以下のファイルは、
wiki.cgi内の変数$modifier_url_dataで指定するURLに対応したディレクトリに転送します。

+-- wiki.css        TEXT        644 (rw-r--r--)     スタイルシート
+-- icon40x40.gif   BINARY      644 (rw-r--r--)     アイコン(小)
+-- icon80x80.gif   BINARY      644 (rw-r--r--)     アイコン(大)

プロバイダによっては、
CGIを置くディレクトリにスタイルシートや画像ファイルを置いても
Webサーバから参照できない場合があります。

その場合には、
Webサーバから参照できる場所のURLを$modifier_url_dataを使って指定し、
そのディレクトリに上記ファイルを転送します。

そのような制限がない場合には、
変数$modifier_url_dataではwiki.cgiを転送したディレクトリを指定し、
同じディレクトリに上記ファイルを転送します。

●作成されるデータ

以下のファイル(deleteme.txt)は、転送する必要はありません。
（転送してもかまいません）
wiki, diff, infoのディレクトリは作成しておく必要があります。

+-- wiki                        777 (rwxrwxrwx)     ディレクトリ
|   +-- deleteme.txt            転送不要
|
+-- diff                        777 (rwxrwxrwx)     ディレクトリ
|   +-- deleteme.txt            転送不要
|
+-- info                        777 (rwxrwxrwx)     ディレクトリ
|   +-- deleteme.txt            転送不要


プロバイダによっては、
CGIを置くディレクトリにあるファイルは、CGIからアクセスできない場合があります。

その場合には、変数$modifier_dir_dataを使って、
「CGIが読み書きできるファイルを置くディレクトリ」を指定しておき、
そのディレクトリに上記のwiki, diff, infoディレクトリを作ります。

そのような制限がない場合には、
変数$modifier_dir_dataではwiki.cgiを転送したディレクトリを指定し、
同じディレクトリに上記のwiki, diff, infoディレクトリを作ります。

-------------------------------------------------
■データのバックアップ方法
-------------------------------------------------

YukiWikiで構築されたWebページのコンテンツは、
wiki.cgiが作り出すデータベース内に保持されます。

作られたデータはすべて
変数$modifier_dir_dataで指定したディレクトリ以下に作られますので、
このディレクトリの下をすべてバックアップしておけばよいでしょう。

変数$modifier_dbtypeを'YukiWikiDB'にした場合には、
wiki, info, diffという3つのディレクトリが作られ、
その下にページごとにファイルが作られます。
バックアップもれがないように注意してください。


-------------------------------------------------
■基本的な使い方
-------------------------------------------------

●新しいページの作り方

1.「新規作成」というリンクをたどります。
2. 新しいページの名前を入力します。
3. ページの内容を入力します。

●テキスト整形のルール

format.txtを参照してください。

●ハイパーリンク

LinkToSomePageやFrontPageのように、
英単語の最初の一文字を大文字にしたものが
二つ以上連続したものはYukiWikiのページ名となり、
それが文章中に含まれるとリンクになります。

二重の大かっこ[[ ]]でくくった文字列も、
YukiWikiのページ名になります。
大かっこの中にはスペースを含めてはいけません。
日本語も使えます。

http://www.hyuki.com/
のようなURLは自動的にリンクになります。


-------------------------------------------------
■謝辞
-------------------------------------------------

本家のWikiを作ったWard Cunninghamに感謝します。
http://c2.com/cgi/wiki

YukiWikiを楽しんで使ってくださるネット上の方々に感謝します。

多くのWikiクローンの作者さんたちと、
YukiWikiのユーザさんたちに深く感謝します。

◆PukiWiki (PHP)
http://pukiwiki.org/
特にInterWiki, 一言コメント機能などに感謝します。

◆Tiki (Ruby)
http://www.todo.org/cgi-bin/jp/tiki.cgi

◆RWiki (Ruby)
http://www.jin.gr.jp/~nahi/RWiki/

◆KbWiki (Perl + HTML::Template)
http://www.hippo2000.info/cgi-bin/KbWiki/KbWiki.pl

◆「極悪」さんのwiki (Perl)
http://hpcgi1.nifty.com/dune/gwiki.pl
特に、YukiWikiDBに感謝します。

◆塚本牧生さんのWalWiki (Perl)
http://digit.que.ne.jp/work/
テーブル機能およびYukiWikiに対する多数の改良に感謝します。

YukiWikiのロゴをデザインしてくださった橋本礼奈さん
http://city.hokkai.or.jp/~reina/
に感謝します。


-------------------------------------------------
■関連リンク
-------------------------------------------------

◆結城浩のページ
http://www.hyuki.com/

◆YukiWikiホームページ
http://www.hyuki.com/yukiwiki/

◆書籍：結城浩のWiki入門
http://www.hyuki.com/wb/

◆本家のWiki
http://c2.com/cgi/wiki?WikiWikiWeb

◆日本発のwikiクローンリスト
http://www1.neweb.ne.jp/wa/yamdas/column/technique/clonelist.html

◆日本発のwikiクローンリスト2
http://www1.neweb.ne.jp/wa/yamdas/column/technique/clonelist2.html
