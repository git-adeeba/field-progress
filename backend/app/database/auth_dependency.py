from fastapi import (
    Depends,
    HTTPException,
)

from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from app.database.supabase import (
    supabase_admin,
    supabase_auth,
)


security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(
        security
    ),
):
    token = credentials.credentials

    try:
        auth_response = (
            supabase_auth
            .auth
            .get_user(
                token
            )
        )

        if not auth_response.user:
            raise HTTPException(
                status_code=401,
                detail=(
                    "Invalid or expired "
                    "authentication token"
                ),
            )

        user = auth_response.user
        user_id = str(
            user.id
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

        if not profile_response.data:
            raise HTTPException(
                status_code=403,
                detail=(
                    "User profile not found"
                ),
            )

        profile = (
            profile_response.data[0]
        )

        return {
            "id":
                user_id,

            "email":
                user.email,

            "profile":
                profile,
        }

    except HTTPException:
        raise

    except Exception as exc:
        print(
            "AUTH ERROR:",
            repr(exc),
        )

        raise HTTPException(
            status_code=401,
            detail=(
                "Invalid or expired "
                "authentication token"
            ),
        )