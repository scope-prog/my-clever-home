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
        """Честное получение объекта лампы с проверкой связи"""
        try:
            bulb = Bulb(self.bulb_ip, effect="smooth", duration=500)
            
            # Стучимся к лампе — запрашиваем её свойства. 
            # Если она выключена из розетки, тут всё упадет в except
            bulb.get_properties() 
            
            print(f"🔌 Реальное подключение к лампе {self.bulb_ip} установлено!")
            return bulb
        except Exception as e:
            print(f"⚠️ Ошибка: Лампа {self.bulb_ip} недоступна (выключена из розетки или не тот IP): {e}")
            return None



class CommandModel(BaseModel):
    sensor: str


@post("/api/v1/command")
async def handle_command(request: Request, data: CommandModel) -> CommandModel:
    return data

@get("/api/v1/light/on")
async def light_on(request: Request) -> dict[str, str]:
    light = SmartLight(bulb_ip=BULB_IP, port=BULB_PORT)
    #вот тут и в таких же местах снизу короч нужно проверять не light а light.bulb
    if light.bulb is None:
        return {"msg": "Соединения нет"}
    else:
        light.bulb.turn_on()
        return {"msg": "Соединение есть"}

@get("/api/v1/light/off")
async def light_off(request: Request) -> dict[str, str]:
    light = SmartLight(bulb_ip=BULB_IP, port=BULB_PORT)
    if light.bulb is None:
        return {"msg": "Соединения нет"}
    else:
        light.bulb.turn_off()
        return {"msg": "Соединение есть"}
    

@get("/api/v1/light")
async def status_light(request: Request) -> dict[str, str]:
    light = SmartLight(bulb_ip=BULB_IP, port=BULB_PORT)
    if light.bulb is None:
        return {"msg": "Соединения нет"}
    else:
        return {"msg": "Соединение есть"}


@get("/")
async def main_page() -> Template:
    return Template(template_name="index.html")


app = Litestar(
    route_handlers=[handle_command, main_page, status_light, light_off, light_on],
    template_config=TemplateConfig(
        directory=Path("templates"),
        engine=JinjaTemplateEngine,
    ),
    debug=True
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app="main:app", host="127.0.0.1", port=8000, reload=True)
