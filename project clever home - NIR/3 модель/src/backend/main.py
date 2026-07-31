from pathlib import Path

from litestar import Litestar, Request, get, post
from litestar.contrib.jinja import JinjaTemplateEngine
from litestar.response import Template
from litestar.template.config import TemplateConfig
from pydantic import BaseModel
from yeelight import Bulb, BulbException

BULB_IP = "192.168.50.21"
BULB_PORT = 55443


class SmartLight:
    def __init__(self, bulb_ip: str, port: int) -> None:
        self.bulb_ip: str = bulb_ip
        self.port: int = port
        self.bulb: Bulb | None = self._get_bulb()

    def _get_bulb(self):
        """Безопасное получение объекта лампы"""
        if self.bulb is not None:
            return self.bulb
        try:
            self.bulb = Bulb(self.bulb_ip, effect="smooth", duration=500)
            print(f"🔌 Подключено к лампе {self.bulb_ip}")
        except Exception as e:
            print(f"⚠️ Ошибка подключения к лампе: {e}")
            self.bulb = None
        return self.bulb


class CommandModel(BaseModel):
    sensor: str


@post("/api/v1/command")
async def handle_command(request: Request, data: CommandModel) -> CommandModel:
    return data


@get("/api/v1/light")
async def status_light(request: Request) -> dict[str, str]:
    light = SmartLight(bulb_ip=BULB_IP, port=BULB_PORT)
    if light is None:
        return {"msg": "Соединения нет"}
    else:
        return {"msg": "Соединение есть"}


@get("/")
async def main_page() -> Template:
    return Template(template_name="index.html")


app = Litestar(
    route_handlers=[handle_command, main_page],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
