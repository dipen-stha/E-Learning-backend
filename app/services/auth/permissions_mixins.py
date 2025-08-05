from typing import Annotated

from fastapi import HTTPException, status

from app.services.enum.users import UserRole
from app.db.models.users import User
from app.services.auth.core import get_current_user

class BaseRoleMixin:
    def __init__(self, user: User):
        self.user = user

    def __call__(self, *args, **kwargs):
        if self.user.is_superuser and self.check_user_role():
            return
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="You do not have permission to perform this action")

    def check_user_role(self):
        pass

class IsAuthenticated(BaseRoleMixin):
    def __call__(self, user: Annotated[User, get_current_user]):
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not Authenticated")
        return


class IsAdmin(BaseRoleMixin):
    def check_user_role(self):
        if self.user.role and self.user.role == UserRole.ADMIN:
            return True
        return False


class IsStudent(BaseRoleMixin):
    def check_user_role(self):
        if self.user.role and self.user.role == UserRole.STUDENT:
            return True
        return False


class IsTutor(BaseRoleMixin):
    def check_user_role(self):
        if self.user.role and self.user.role == UserRole.TUTOR:
            return True
        return False
