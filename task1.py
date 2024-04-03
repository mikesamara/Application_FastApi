'''
Создать веб-приложение на FastAPI, которое будет предоставлять API для
работы с базой данных пользователей. Пользователь должен иметь
следующие поля:
○ ID (автоматически генерируется при создании пользователя)
○ Имя (строка, не менее 2 символов)
○ Фамилия (строка, не менее 2 символов)
○ Дата рождения (строка в формате "YYYY-MM-DD")
○ Email (строка, валидный email)
○ Адрес (строка, не менее 5 символов)
Погружение в Python
Задание №2 (продолжение)
API должен поддерживать следующие операции:
○ Добавление пользователя в базу данных
○ Получение списка всех пользователей в базе данных
○ Получение пользователя по ID
○ Обновление пользователя по ID
○ Удаление пользователя по ID
Приложение должно использовать базу данных SQLite3 для хранения
пользователей.
'''
import random
from typing import List

from pydantic import Field, EmailStr
import databases
import sqlalchemy
from fastapi import FastAPI
from pydantic import BaseModel
from sqlalchemy import create_engine

DATABASE_URL = "sqlite:///mydatabase1.db"

database = databases.Database(DATABASE_URL)

metadata = sqlalchemy.MetaData()

users = sqlalchemy.Table(
    "users",
    metadata,
    sqlalchemy.Column("user_id", sqlalchemy.Integer, primary_key=True),
    sqlalchemy.Column("username", sqlalchemy.String(32)),
    sqlalchemy.Column('last_name', sqlalchemy.String(32)),
    sqlalchemy.Column("birth_day", sqlalchemy.String),
    sqlalchemy.Column("email", sqlalchemy.String(128)),
    sqlalchemy.Column("adress", sqlalchemy.String(128))
)

engine = create_engine(DATABASE_URL)
metadata.create_all(engine)

app = FastAPI()


class User(BaseModel):
    user_id: int
    username: str = Field(title='username', min_length=2)
    last_name: str = Field(title='last_name', min_length=2)
    birth_day: str = Field(title='birth_day')
    email: EmailStr = Field(title='email', max_length=32)
    adress: str = Field(title='adress', min_length=5)


@app.on_event("startup")
async def startup():
    await database.connect()


@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()


@app.get("/fake_users/{count}")
async def fake_users(count: int):
    for i in range(count):
        guery = users.insert().values(username=f'user{i}',
                                      last_name=f'user{i}',
                                      birth_day=f'{random.randint(1, 31):02d}.{random.randint(1, 12):02d}.{random.randint(1970, 2020)}',
                                      email=f'user{i}@email.ru', adress=f'Username{i}')
        await database.execute(guery)
    return {'message': f'{count} fake users create'}


@app.get('/users/', response_model=List[User])
async def read_users():
    query = users.select()
    return await database.fetch_all(query)


@app.get('/users/{user_id}/', response_model=User)
async def read_user(id_user: int):
    guery = users.select().where(users.c.user_id == id_user)
    return await database.fetch_one(guery)


@app.post('/users/', response_model=User)
async def create_user(user: User):
    query = users.insert().values(
        username=user.username,
        last_name=user.last_name,
        birth_day=user.birth_day,
        email=user.email,
        adress=user.adress
    )
    user.user_id = await database.execute(query)
    return user


@app.put('/users/{user_id}')
async def update_user(id_user: int, new_user: User):
    query = users.update().where(users.c.user_id == id_user).values(
        username=new_user.username,
        last_name=new_user.last_name,
        birth_day=new_user.birth_day,
        email=new_user.email,
        adress=new_user.adress
    ).returning(users.c.user_id)
    updated_user_id = await database.execute(query)
    return updated_user_id


@app.delete('/users/{user_id}')
async def delete_user(id_user: int):
    query = users.delete().where(users.c.user_id == id_user)
    await database.execute(query)
    return {'message': 'User deleted'}
