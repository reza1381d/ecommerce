from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.users.models import User


SORT_COLUMNS = {
    "id": User.id,
    "email": func.lower(User.email),
    "first_name": func.lower(User.first_name),
    "last_name": func.lower(User.last_name),
    "role": func.lower(User.role),
    "created_at": User.created_at,
}


def list_users(
    db: Session,
    page: int,
    limit: int,
    search: str | None,
    sort_by: str,
    sort_order: str,
) -> tuple[list[User], int]:
    conditions = []

    if search and search.strip():
        term = search.strip()
        escaped_term = (
            term.replace("\\", "\\\\")
            .replace("%", "\\%")
            .replace("_", "\\_")
        )
        pattern = f"%{escaped_term}%"

        search_conditions = [
            User.email.ilike(pattern, escape="\\"),
            User.first_name.ilike(pattern, escape="\\"),
            User.last_name.ilike(pattern, escape="\\"),
            User.role.ilike(pattern, escape="\\"),
        ]

        if User.phone is not None:
            search_conditions.append(
                User.phone.ilike(pattern, escape="\\")
            )

        if term.isdigit():
            search_conditions.append(User.id == int(term))

        conditions.append(or_(*search_conditions))

    query = select(User)
    count_query = select(func.count()).select_from(User)

    if conditions:
        query = query.where(*conditions)
        count_query = count_query.where(*conditions)

    sort_column = SORT_COLUMNS[sort_by]
    ordering = (
        sort_column.desc()
        if sort_order == "desc"
        else sort_column.asc()
    )

    query = query.order_by(ordering)

    # ترتیب ثانویه باعث صفحه‌بندی باثبات هنگام مقادیر تکراری می‌شود.
    if sort_by != "id":
        query = query.order_by(User.id.asc())

    offset = (page - 1) * limit
    users = list(
        db.scalars(query.offset(offset).limit(limit)).all()
    )
    total = db.scalar(count_query) or 0

    return users, total