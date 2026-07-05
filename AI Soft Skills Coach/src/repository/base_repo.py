from __future__ import annotations

from typing import Any, Generic, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

ModelType = TypeVar("ModelType")


class BaseRepository(Generic[ModelType]):
    def __init__(self, session: AsyncSession, model: type[ModelType]):
        self.session = session
        self.model = model

    async def create(self, obj: ModelType):
        self.session.add(obj)
        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def get_by_id(self, obj_id: Any):
        return await self.session.get(self.model, obj_id)

    async def get_one_by(self, **filters: Any):
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return result.scalar_one_or_none()

    async def list_all(self):
        result = await self.session.execute(select(self.model))
        return list(result.scalars().all())

    async def list_by(self, **filters: Any):
        result = await self.session.execute(select(self.model).filter_by(**filters))
        return list(result.scalars().all())

    async def update_by_id(self, obj_id: Any, data: dict[str, Any]):
        obj = await self.get_by_id(obj_id)
        if obj is None:
            return None

        for key, value in data.items():
            setattr(obj, key, value)

        await self.session.flush()
        await self.session.refresh(obj)
        return obj

    async def delete_by_id(self, obj_id: Any):
        obj = await self.get_by_id(obj_id)
        if obj is None:
            return False

        await self.session.delete(obj)
        await self.session.flush()
        return True
