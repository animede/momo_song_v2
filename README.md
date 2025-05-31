# momo_song_v2

5月31日　最新版

ACE-Stepのgradio-clientによるAPIアクセスをFastAPIでラップ。

　→音楽生成サーバを独立したサーバで動かすことが出来ます。
 
 ##方法
 ace_server.pyをACE-Stepディレクトリにコピー
 
 ACE-Stepのデモアプリを動かします。5月15日にバージョンアップしているので、以下のコマンドになります。
 
 acestep --port 7865  --torch_compile true --cpu_offload true --overlapped_decode true

 その後、新たにターミナルを開き、ACE-Stepディレクトリに移動してFastAPIサーバを起動

 python ace_server.py　

 これで、ローカルアドレスまたは。動かしたPCのipアドレスで生成リクエストを受け付けることが出来ます。

 Responceは
 mp3オーディオとpngイメージです。

 momo_song_v2へ移り、music_server本体を動かします。

 python　music_server.py

 ブラウザから

 http://localhost:64653

 で起動hします。
