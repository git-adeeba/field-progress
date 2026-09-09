from fastapi import (
    APIRouter,
    HTTPException,
)

from pydantic import (
    BaseModel,
    EmailStr,
)

from app.database.supabase import (
    supabase_admin,
    supabase_auth,
)


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"],
)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


@router.post("/login")
def login(
    data: LoginRequest,
):
    try:
        auth_response = (
            supabase_auth
            .auth
            .sign_in_with_password(
                {
                    "email":
                        data.email,

                    "password":
                        data.password,
                }
            )
        )

        if (
            not auth_response.user
            or not auth_response.session
        ):
            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid email "
                    "or password"
                ),
            )

        user_id = str(
            auth_response.user.id
        )

        profile_response = (
            supabase_admin
            .table("profiles")
            .select(
                "id,"
                "full_name,"
                "role,"
                "department,"
                "created_at"
            )
            .eq(
                "id",
                user_id,
            )
            .limit(1)
            .execute()
        )

        profile = (
            profile_response.data[0]
            if profile_response.data
            else None
        )

        if not profile:
            raise HTTPException(
                status_code=403,
                detail=(
                    "User profile not found"
                ),
            )

        return {
            "access_token":
                auth_response
                .session
                .access_token,

            "refresh_token":
                auth_response
                .session
                .refresh_token,

            "token_type":
                "bearer",

            "user": {
                "id":
                    user_id,

                "email":
                    auth_response
                    .user
                    .email,
            },

            "profile":
                profile,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "LOGIN ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=401,
            detail="Login failed",
        )