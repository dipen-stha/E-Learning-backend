from typing import Annotated

from fastapi import Depends, HTTPException, status

from app.db.models.users import User
from app.services.auth.core import get_current_user
from app.services.enum.users import UserRole


class BaseRoleMixin:
    def __init__(self, required_role: UserRole | None = None):
        self.required_role = required_role

    def __call__(self, user: Annotated[User, Depends(get_current_user)]) -> User:
        # Must be authenticated
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authenticated"
            )

        # Superusers can bypass role check
        if user.is_superuser:
            return user
        # Role check if required
        if self.required_role and user.profile.role != self.required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have permission to perform this action",
            )

        return user


class IsAuthenticated(BaseRoleMixin):
    def __init__(self):
        super().__init__(None)  # just requires authentication


class IsAdmin(BaseRoleMixin):
    def __init__(self):
        super().__init__(UserRole.ADMIN)


class IsStudent(BaseRoleMixin):
    def __init__(self):
        super().__init__(UserRole.STUDENT)


class IsTutor(BaseRoleMixin):
    def __init__(self):
        super().__init__(UserRole.TUTOR)
