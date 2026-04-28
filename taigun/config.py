from dataclasses import dataclass


@dataclass
class Profile:
    host: str
    port: int
    database: str
    username: str
    password: str
    acting_user: str
