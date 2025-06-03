import json
import asyncio
import re
from textwrap import dedent
import pygame
from openai_chat import chat_req,AsyncOpenAI
from create_image_world import create_image
import requests

#---------------- OpenAI API -----------------
a_client =AsyncOpenAI(
    #base_url="http://127.0.0.1:8080/v1",
    base_url="http://39.110.248.77:64652/v1", # 27B
    #base_url="http://39.110.248.77:64650/v1", # 27B
    api_key="YOUR_OPENAI_API_KEY",  # このままでOK
    )

#sdxl_url = 'http://0.0.0.0:64656'
sdxl_url = 'http://39.110.248.77:64656'

# 音楽生成のためのAPIクライアント
#ace_url = "http://192.168.5.99:64756/generate"#
ace_url = "http://39.110.248.77:64756/generate"#

# Pygameの初期化
pygame.mixer.init()

async def llm(user_msg):
    print("LLM")
    response_json = await chat_req(a_client, user_msg, "あなたは賢いAIです。userの要求や質問に正しく答えること")
    return {"message": response_json}

async def music_generation(user_input,genre_tags):
    print("=====>>>>>user_input=",user_input)
    request_song = dedent(f"""
        ユーザーの入力の意図を正確に判断して選択肢から選び、指定されたワードを返しなさい。選択肢->
        1) autoや、おまかせの場合の指定ワードは'generatSong',
        2) 歌詞を指定している場合の指定ワードは'lyrics',
        3) 曲のジャンルやテーマを入力している場合の指定ワードは'genre',
        4) 歌詞の雰囲気を入力していると判断できる場合の指定ワードは'theme',
        5) 曲のタイトルを入力していると判断できる場合の指定ワードは'title',
        検出された指定ワードは、json内に記載すること。
        user_inputにタイトル、ジャンル、ムード、楽器について記載がある場合は、各々をjesonのtitle、genre、atmosphereにinstruments記載すること。
        json形式は以下の通りとする。必ずすべてのキーを記載すること。必ずjson形式で出力すること。
        楽器が記載されている場合は、genreに追加すること。
        ただし、json形式の出力は以下のようにコードブロックで囲むこと。
        ```json
        {{"word": "指定ワード","title":"タイトル", "lyrics": "歌詞", "genre": "ジャンル", "theme": "テーマ", "atmosphere": "歌詞の雰囲気","instruments","楽器"}}
        該当がない場合の指定ワードはnullです。「これで良いか聞いてください」のような確認文は使ってはいけません。
        ユーザーの入力={user_input}
    """).strip()
    print("request_song=", request_song)
    response =  await  llm(request_song)
    print("response=", response)
    # 正規表現でJSON部分を抽出
    regex = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(regex, response['message'])

    if match:
        json_string = match.group(1)  # マッチしたJSON部分を取得
        try:
            json_data = json.loads(json_string)  # JSON文字列を辞書に変換
            print("抽出されたJSONデータ:", json_data)
        except json.JSONDecodeError as e:
            print("JSONのパースに失敗しました:", e)
            return False, None, None, None
    else:
        print("JSON部分が見つかりませんでした。")
        return False, None, None, None
    sel_word = json_data.get('word', None)
    print("sel_word=", sel_word)

    # sel_wordから処理を分岐
    if sel_word == "generatSong":
        song_generate = "音楽の生成をする場合のタイトルを一つだけ提案してください。\
            タイトルは様々な場面や時間、景色、思い、人、モノ、世界など、音楽のタイトルに相応しいことを想定して多彩で変化に富む内容を考えること。\
            例えは、故郷、夕暮れ、星、思い出、愛、旅、夢、静か、夜、都会、山、海、アニメ、ロボット、AI、未来、過去、世界、日本、大阪、東京、その他の都市、など、\
            これ以外も考慮しつつ多彩なテーマからタイトルを選ぶ。音楽のジャンルや雰囲気をから考えるのも効果的です。\
            LLMの持つ特性に偏りがちなので自らの特性にこだわらないタイトルを考えること。タイトルは必ず記入すること。内容だけで説明は不要です。\
            タイトルは日本で作成して下さい"
        response = await llm(song_generate)
        print("おまかせesponse=", response)
        return await music_generation(response,genre_tags)  # 再帰的に呼び出し
    elif sel_word in ["lyrics", "genre", "theme", "atmosphere",'title']:
        return await gen_lyrics(json_data['title'],json_data['lyrics'], json_data['genre'], json_data['theme'], json_data['atmosphere'],json_data['instruments'],genre_tags)
    else:
        print("genSong_qaで正しい選択肢が得られなかった")
        return False, None, None, None


#　歌詞、ジャンル、テーマ,雰囲気　から作詞と作曲をする
async def gen_lyrics(title,lyrics, genre, theme, atmosphere,instruments,genre_tags):
    json_data = {
        "title":title,
        "lyrics": lyrics,
        "genre": genre,
        "theme": theme,
        "atmosphere": atmosphere,
        "instruments":instruments,
    }
    request_msg = dedent(f"""
        jsonDataで示されたユーザーの作曲の意図を正確に判断して作詞のための指定されたlyrics形式と作曲のためのgenreを作成しなさい。
        title、歌詞、ジャンル、ムード（雰囲気）、楽器はユーザー入力に記載があればそのまま採用すること。
        ただし、ジャンル、ムード（雰囲気）、楽器は日本語で入力された場合はそのまま採用せず、必ず英語に翻訳すること。
         "genre"については、ユーザーの入力を採用しても、追加で曲の雰囲気にある、他のタグを追加しても構いません。        
        lyrics形式を作成するきには、ユーザーのリクエストの"lyrics"に歌詞ががあればそのまま変形せずに歌詞として使ってlyrics形式を作成すること。
        ユーザーのリクエストの"lyrics"がすでにlyrics形式の場合はそのまま採用すること。
        ユーザーのリクエストの"lyrics"に歌詞がない場合のlyrics形式は、歌詞の内容を表すものとして、曲のジャンルやテーマ、歌詞の雰囲気を考慮して作成すること。
        英語の歌詞は書いてはいけません。英単語も使ってはいけません。更に日本語以外、他のどのような言語も使わないこと。
        ユーザーのクエストに長さ指定のような記載があれば従ってください、無ければ15行前後の歌詞を作成すること。30行よりも長い歌詞は作成しないこと。
        lyricsの形式の見本は以下のとおりです。ただし、詞や曲の内容に応じて、"verse"、"chorus", "bridge", "outro"を作曲の理論を参照しつつ、組み合わせること。
        "verse"、"chorus", "bridge"は複数回使っても構いません。形式は必ず"verse"、"chorus", "bridge", "outro"を1回以上使う恋と。
        "verse1","verse2"のように複数回使うことも可能です。曲の雰囲気に合わせて、慎重に考えてください。
        歌詞の形式の基本的な見本={{"verse": "歌詞の内容", "chorus": "歌詞の内容", "bridge": "歌詞の内容", "outro": "歌詞の内容"}}
        genreの作成は以下のタグが定義されたjsonを参考にしてください。
        'genre'、'instrument'、'mood'、'gender'、'timbre'の各キーから必要に応じて一つ以上のタグを採用してください。
        genre作成用json={json.dumps(genre_tags, ensure_ascii=False)}
        作成したlyrics形式は、以下のjson形式のlyricsの要素に記載すること。各要素は必ず記入すること。出力のjson形式は以下の通りです。
        {{"title": "タイトル", "lyrics": "歌詞", "genre": "ジャンル", "theme": "テーマ", "atmosphere": "雰囲気"}}
        解説は不要です。参考にするユーザーのリクエストは以下のjson形式で示します。
        jsonData={json.dumps(json_data, ensure_ascii=False)}
    """).strip()

    #print("request_msg=", request_msg)
    print("Setuo prompt for generate lyrics & genere")
    response = await llm(request_msg)

    # 正規表現でJSON部分を抽出
    regex = r'```json\s*([\s\S]*?)\s*```'
    match = re.search(regex, response["message"])
    json_data_m2 = {}
    if match and match[1]:
        json_string = match[1]
        try:
            json_data_m2 = json.loads(json_string)
            print("Extracted JSON object jsonData_m2:", json_data_m2)
            result = True
        except json.JSONDecodeError as error:
            print("JSON のパースに失敗しました:", error)
            result = False
    else:
        print("JSON 部分が見つかりませんでした。")
        result = False

    if result:
        end_detail = dedent(f"""
            作曲ができたので、歌詞部分だけを抜き出して表示してください。
            ただし、verse、chorus、bridge、outroの各単語は文章には入れないでください。
            歌詞の表示は、改行で区切って出力すること。その後に曲の説明と意図を簡単に説明してください。
            曲の説明には曲が完成したことには触れないこと。
            曲のタイトルは'title'キーに、歌詞は'lyrics'キーに、曲のジャンルは'genre'キーにあります。
            その他の情報は'theme'、'atmosphere'のキーに記載されています。
            各々記載の内容は説明してもいいけど、キーやjsonの形式のデータは出力には入れないこと。
            コメントは、簡潔に説明すること。作曲の結果は次のjson形式で示します。
            作曲結果は以下の通りです。
            {json.dumps(json_data_m2, ensure_ascii=False)}
        """).strip()

        music_world = await llm(end_detail)
        lyrics_m = "test"
        return result, json_data_m2, music_world, lyrics_m
    else:
        return result, None, None, None

def convert_lyrics_dict_to_text(lyrics_dict):
    if not isinstance(lyrics_dict, dict):
        print(f"XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX  lyrics_dictは辞書型である必要があります。現在の型: {type(lyrics_dict)}")
        return lyrics_dict
    result=""
    for key, value in lyrics_dict.items():
        if not isinstance(value, str):
            print(f"警告: 値が文字列ではありません。スキップします。キー: {key}, 値: {value}")
            continue
        processed_key = re.sub(r"[（(].*?[）)]", "", key).strip()
        processed_value = re.sub(r"^[（(].*?[）)]\s*\n?", "", value)
        result += f"[{processed_key}]\n{processed_value}\n"
    return result

# 各キーの値をカンマ区切りで結合し、テキスト形式に変換
def convert_genre_to_text(genre_data):
    result = []
    for key, values in genre_data.items():
        # キーと値を結合してテキスト形式に変換
        result.append(f"{key}: {', '.join(values)}")
    return "\n".join(result)

# ++++++++++++++++++++++++　歌の生成　+++++++++++++++++++++++
def generate_song(jeson_song: dict,infer_step: int = 27,guidance_scale: float = 15,omega_scale: float = 10):
    # JSON 文字列化
    print("======>>>>>jeson_song=",jeson_song)
    lyrics_dic = jeson_song['lyrics']
    print("###### lyrics_dic >>>>",lyrics_dic)
    lyrics = convert_lyrics_dict_to_text(lyrics_dic)
    print("###### lyrics_text >>>>",lyrics)
    genre = jeson_song['genre']
    print("###### genre >>>>",genre)
    # APIに送信するデータの準備
    data = {
        "audio_duration": -1,
        "genre": genre,
        "infer_step": infer_step,
        "lyrics": lyrics,
        "guidance_scale": guidance_scale,
        "scheduler_type": "euler",
        "cfg_type": "apg",
        "omega_scale": omega_scale,
        "guidance_interval": 0.5,
        "guidance_interval_decay": 0.0,
        "min_guidance_scale": 3,
        "guidance_scale_text": 0.0,
        "guidance_scale_lyric": 0.0
    }
    response = requests.post(ace_url , data=data)
    # サーバからのContent-Dispositionヘッダーからファイル名を抽出
    cd = response.headers.get("Content-Disposition", "")
    match = re.search(r'filename="?([^"]+)"?', cd)
    filename = match.group(1) if match else "output.mp3"
    return response.content

#音楽ファイルを再生する関数。 Args: audio_data_path: 音楽ファイルのパス
def play_music(audio_data_path):
    try:
        pygame.mixer.music.load(audio_data_path)
        # 再生
        pygame.mixer.music.play()
        print(f"再生中: {audio_data_path}")
        # 再生が終了するまで待機
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
    except Exception as e:
        print(f"音楽の再生中にエラーが発生しました: {e}")
        
async def maine():  # 非同期関数として定義
    user_input = input("ユーザーの入力をしてください。")
    result, json_data_m2, music_world, lyrics_m = await music_generation(user_input)
    print("lyrics_m=", lyrics_m)
    print("music_world=", music_world)
    print("lyrics_dic=", json_data_m2)
    if not result:
        print("音楽の生成に失敗しました。")
        return
    infer_step = 150
    guidance_scale = 15
    omega_scale = 10
    audio_data_path = generate_song(json_data_m2, infer_step, guidance_scale, omega_scale)

    # 歌詞からイメージを生成
    pil_image = await create_image(sdxl_url,a_client, music_world, "text2image", "t2i")
    pil_image.show()

    # 音楽の生成が成功した場合、音楽を再生
    play_music("/home/animede/ACE-Step/"+audio_data_path)

if __name__ == "__main__":
    asyncio.run(maine())  # asyncio.runで非同期関数を実行
