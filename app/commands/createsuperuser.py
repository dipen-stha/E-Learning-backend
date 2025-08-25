from datetime import date

from app.db.models.users import User, Profile
from app.db.session.session import get_db
from app.services.auth.hash import get_password_hash
from app.services.enum.users import UserGender
from app.services.utils.validator import validate_email


def create_superuser():
    name=input("Enter name: ")
    username = input("Enter username: ")
    email = input("Enter email: ")
    password = input("Enter password: ")
    repeat_password = input("Repeat password: ")

    if not password == repeat_password:
        print("Passwords do not match")
        return
    if not validate_email(email):
        print("Enter a valid email")
        return

    hashed_password = get_password_hash(password)
    user = User(
        username=username,
        password=hashed_password,
        email=email,
        is_superuser=True,
    )
    session = next(get_db())
    session.add(user)
    session.flush()
    user_profile = Profile(
        user_id=user.id,
        name=name,
        dob=date(1999,1,1),
        gender=UserGender.MALE
    )
    session.add(user_profile)
    session.commit()

    print(f"Superuser created with username: {user.username}")


if __name__ == "__main__":
    create_superuser()
