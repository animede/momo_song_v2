
from fastapi import FastAPI, Form, Response
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
import io, base64, json, os
from gradio_client import Client

app = FastAPI()

m_client = Client("http://127.0.0.1:7865/")

@app.post('/generate')
async def generate(
    audio_duration: float = Form(-1),
    genre: str = Form(...),
    infer_step: int = Form(50),
    lyrics: str = Form(...),
    guidance_scale: float = Form(15),
    scheduler_type: str = Form("euler"),
    cfg_type: str = Form("apg"),
    omega_scale: float = Form(...),
    guidance_interval: float = Form(0.5),
    guidance_interval_decay: float = Form(0.0),
    min_guidance_scale: float = Form(3),
    use_erg_tag: bool = Form(True),
    use_erg_lyric: bool = Form(True),
    use_erg_diffusion: bool = Form(True),
    guidance_scale_text: float = Form(0.0),
    guidance_scale_lyric: float = Form(0.0)
):
    result = m_client.predict(
        format="mp3",
        audio_duration=audio_duration,
        prompt=genre,
        lyrics=lyrics,
        infer_step=infer_step,
        guidance_scale=guidance_scale,
        scheduler_type=scheduler_type,
        cfg_type=cfg_type,
        omega_scale=omega_scale,
        manual_seeds=None,
        guidance_interval=guidance_interval,
        guidance_interval_decay=guidance_interval_decay,
        min_guidance_scale=min_guidance_scale,
        use_erg_tag=use_erg_tag,
        use_erg_lyric=use_erg_lyric,
        use_erg_diffusion=use_erg_diffusion,
        oss_steps=None,
        guidance_scale_text=guidance_scale_text,
        guidance_scale_lyric=guidance_scale_lyric,
        api_name="/text2music"
    )
    filename = result[1]["audio_path"]
    audio_path = result[1]["audio_path"]
    print(f"Generated audio file path: {audio_path}")
    with open(audio_path, "rb") as f:
        audio_bytes = f.read()
    return Response(
        content=audio_bytes,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'}
    )

if __name__ == '__main__':
    import uvicorn
    uvicorn.run('ace_server:app', host='0.0.0.0', port=64756, reload=True)
