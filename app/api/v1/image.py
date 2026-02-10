from fastapi import APIRouter, Form
from app.api.v1.controllers.image.tweet_controller import tweet_image_handler

router = APIRouter()


@router.post("/tweet")
async def tweet_image_route(text: str = Form(...), return_file: bool = Form(True)):
    return await tweet_image_handler(text, return_file)
