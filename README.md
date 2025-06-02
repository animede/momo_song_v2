# momo_song_v2

5月31日　最新版

## 機能追加

１）ACE-Stepのgradio-clientによるAPIアクセスをFastAPIでラップ。

　→音楽生成サーバを独立したサーバで動かすことが出来ます。
２）自動連続生成機能
　-自動生成チェックBOXを有効にすれば、音楽終了後に自動的に生成が始まります

 何らかの操作でチェックが外れるので、生成ボタンクリック後に有効にすることをおすすめします

 自動生成チェックBOXを有効にして何も操作をしないと120秒後に生成が始まります。

 生成エラーが発生すると、音楽生成がなので、120秒タイマーが働いて120秒後に生成が再開します。
 
 ## 起動方法
 ace_server.pyをACE-Stepディレクトリにコピー
 
 ACE-Stepのデモアプリを動かします。5月15日にバージョンアップしているので、以下のコマンドになります。
 
 acestep --port 7865  --torch_compile true --cpu_offload true --overlapped_decode true

 その後、新たにターミナルを開き、ACE-Stepディレクトリに移動してFastAPIサーバを起動

 python ace_server.py　

 これで、ローカルアドレスまたは。動かしたPCのipアドレスで生成リクエストを受け付けることが出来ます。

 Responceは
 mp3オーディオとpngイメージです。

 再度、ターミナルを開いて、ACE-Stepで作成した環境を有効にします。

 momo_song_v2へ移り、music_server本体を動かします。

事前に以下モジュールをインストール。もし起動時にモジュールがないとメッセージが出たら追加Hしてください。

　asyncio

　pygame

　openai

　pillow

起動コマンド

python　music_server.py

 ブラウザから

 http://localhost:64653

 で起動hします。
## ローカルLLMを使用しない場合
base_urlを使用するサービスのAPIアドレスに変更、api_keyに各自取得しているキーそ記載

 music_server.pyの
 
    a_client =AsyncOpenAI(
        base_url="http://39.110.248.77:64650/v1", # 27B　PC1
        api_key="YOUR_OPENAI_API_KEY",  # このままでOK
        )

## 画像を生成しない場合

 music_server.pyの

     # ① 音楽生成の結果を取得
    #generate_song から bytes が返ってくる想定
    # 並列処理で音楽と画像を生成
    audio_task = asyncio.to_thread(generate_song, lyrics_dict, infer_step, guidance_scale, gomega_scale)
    image_task = create_image(sdxl_url, a_client, music_world, "text2image", "t2i")
    audio_bytes, pil_image = await asyncio.gather(audio_task, image_task)
    buf = io.BytesIO()
    pil_image.save(buf, format='PNG')
    image_base64 = 'data:image/png;base64,' + __import__('base64').b64encode(buf.getvalue()).decode()
    # ④ 音声も Base64 にエンコード（Data URI スキーム）
    audio_base64 = 'data:audio/mp3;base64,' + base64.b64encode(audio_bytes).decode()
    # ⑤ JSON でまとめて返却
    print("generate_music_result:lyrics_dict =", lyrics_dict)
    return JSONResponse({
        'lyrics_json': json.dumps(lyrics_dict, ensure_ascii=False, indent=2),
        'image_base64': image_base64,
        'audio_base64': audio_base64,
    })

    を
        # ① 音楽生成の結果を取得
    #generate_song から bytes が返ってくる想定
    # 並列処理で音楽と画像を生成
    audio_task = asyncio.to_thread(generate_song, lyrics_dict, infer_step, guidance_scale, gomega_scale)
    audio_bytes = await asyncio.gather(audio_task)
    buf = io.BytesIO()
    #ここで適当なイメージを読み込んでbase64に変換し以下の部分で代入
    image_base64 = 
    
    # ④ 音声も Base64 にエンコード（Data URI スキーム）
    audio_base64 = 'data:audio/mp3;base64,' + base64.b64encode(audio_bytes).decode()
    # ⑤ JSON でまとめて返却
    print("generate_music_result:lyrics_dict =", lyrics_dict)
    return JSONResponse({
        'lyrics_json': json.dumps(lyrics_dict, ensure_ascii=False, indent=2),
        'image_base64': image_base64,
        'audio_base64': audio_base64,
    })
