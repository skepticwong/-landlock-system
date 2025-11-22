# backend/models/plot.py
from datetime import datetime
from db.supabase import db

class Plot:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.plot_name = kwargs.get('plot_name')
        self.owner_phone = kwargs.get('owner_phone')
        self.points = kwargs.get('points', [])
        self.area = kwargs.get('area')
        self.status = kwargs.get('status', 'pending')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())
        self.user_id = kwargs.get('user_id')

    @classmethod
    def from_db(cls, data):
        if not data:
            return None
        if isinstance(data, list):
            return [cls(**plot) for plot in data]
        return cls(**data)

    @classmethod
    async def get_by_id(cls, plot_id: str):
        result = db.select("plots", eq={"id": plot_id})
        return cls.from_db(result[0] if result else None)

    @classmethod
    async def get_by_owner(cls, user_id: str):
        result = db.select("plots", eq={"user_id": user_id}, order="created_at.desc")
        return cls.from_db(result)

    @classmethod
    async def create(cls, plot_data: dict):
        plot_data['created_at'] = datetime.utcnow().isoformat()
        plot_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = db.insert("plots", [plot_data])
        return cls.from_db(result[0] if result else None)

    async def update(self, update_data: dict):
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = db.update(
            "plots",
            update_data,
            eq={"id": self.id}
        )
        if result:
            for key, value in update_data.items():
                setattr(self, key, value)
        return bool(result)

    async def delete(self):
        return db.delete("plots", eq={"id": self.id})

    def to_dict(self):
        return {
            "id": self.id,
            "plot_name": self.plot_name,
            "owner_phone": self.owner_phone,
            "points": self.points,
            "area": self.area,
            "status": self.status,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "user_id": self.user_id
        }