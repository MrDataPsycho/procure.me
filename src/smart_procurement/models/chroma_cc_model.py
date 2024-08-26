from pydantic import BaseModel
from typing import List


class CommodityCodes(BaseModel):
    l1: int
    l1_desc: str
    l2: int
    l2_desc: str
    l3: int
    l3_desc: str

    def get_metadata_as_dict(self):
        data = self.model_dump()
        data.pop('l3_desc', None)
        data.pop('l3', None)
        return data

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            l1=data.get('l1'),
            l1_desc=data.get('l1_desc'),
            l2=data.get('l2'),
            l2_desc=data.get('l2_desc'),
            l3=data.get('l3'),
            l3_desc=data.get('l3_desc')
        )


class CommodityCodesListChromaDB(BaseModel):
    codes: List[CommodityCodes]

    def get_chroma_input_document(self):
        return dict(
            ids=[str(item.l3) for item in self.codes],
            metadatas=[item.get_metadata_as_dict() for item in self.codes],
            documents=[item.l3_desc for item in self.codes],
        )

    @classmethod
    def from_dict(cls, data: List[dict]):
        return cls(codes=[CommodityCodes.from_dict(item) for item in data])
