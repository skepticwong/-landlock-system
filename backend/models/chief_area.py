# backend/models/chief_area.py
from datetime import datetime
from db.sqlite_db import db
from data.geographic_areas import get_area_name

class ChiefArea:
    def __init__(self, **kwargs):
        self.id = kwargs.get('id')
        self.chief_id = kwargs.get('chief_id')
        self.area_type = kwargs.get('area_type')
        self.area_id = kwargs.get('area_id')
        self.area_name = kwargs.get('area_name')
        self.created_at = kwargs.get('created_at', datetime.utcnow().isoformat())
        self.updated_at = kwargs.get('updated_at', datetime.utcnow().isoformat())

    @classmethod
    def from_db(cls, data):
        if not data:
            return None
        if isinstance(data, list):
            return [cls(**area) for area in data]
        return cls(**data)

    @classmethod
    async def get_by_id(cls, area_id: str):
        result = db.select("chief_areas", eq={"id": area_id})
        area = result[0] if result else None
        return cls.from_db(area)

    @classmethod
    async def get_by_chief(cls, chief_id: str):
        result = db.select("chief_areas", eq={"chief_id": chief_id})
        return cls.from_db(result)

    @classmethod
    async def get_all(cls):
        result = db.select("chief_areas", order="created_at DESC")
        return cls.from_db(result)

    @classmethod
    async def create(cls, area_data: dict):
        area_data['created_at'] = datetime.utcnow().isoformat()
        area_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = db.insert("chief_areas", [area_data])
        return cls.from_db(result[0] if result else None)

    async def update(self, update_data: dict):
        update_data['updated_at'] = datetime.utcnow().isoformat()
        
        result = db.update(
            "chief_areas",
            update_data,
            eq={"id": self.id}
        )
        if result:
            for key, value in update_data.items():
                setattr(self, key, value)
        return bool(result)

    async def delete(self):
        return db.delete("chief_areas", eq={"id": self.id})

    def to_dict(self):
        return {
            "id": self.id,
            "chief_id": self.chief_id,
            "area_type": self.area_type,
            "area_id": self.area_id,
            "area_name": self.area_name,
            "created_at": self.created_at,
            "updated_at": self.updated_at
        }

    def contains_plot(self, plot_data: dict) -> bool:
        """Check if a plot is within the chief's predefined area based on district/TA/village"""
        if not self.area_type or not self.area_id:
            return False
        
        plot_district = plot_data.get('district', '').lower()
        plot_ta = plot_data.get('traditional_authority', '').lower()
        plot_village = plot_data.get('village', '').lower()
        
        if self.area_type == 'district':
            # Match by district name (case-insensitive)
            return plot_district == self.area_id.lower() or plot_district in self.area_name.lower()
        elif self.area_type == 'traditional_authority':
            # Match by traditional authority name (case-insensitive)
            return plot_ta == self.area_id.lower() or plot_ta in self.area_name.lower()
        elif self.area_type == 'village':
            # Match by village name (case-insensitive)
            return plot_village == self.area_id.lower() or plot_village in self.area_name.lower()
        
        return False
