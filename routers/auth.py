from fastapi import APIRouter

router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)

@router.get("/")
async def get_helloworld():
    return "Hello World"