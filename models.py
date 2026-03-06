from dataclasses import dataclass, asdict
import uuid


@dataclass
class Order:
    symbol: str
    quantity: float
    price: float
    order_id: str = None

    def __post_init__(self):
        if self.order_id is None:
            self.order_id = str(uuid.uuid4())

    def as_dict(self):
        return asdict(self)
