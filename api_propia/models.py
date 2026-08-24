from datetime import datetime

from pydantic import BaseModel, Field


class SolicitudEntrada(BaseModel):
    asunto: str = Field(min_length=5, max_length=200)
    descripcion: str | None = Field(default=None, max_length=4000)
    area: str = Field(min_length=2, max_length=80)
    solicitante: str = Field(min_length=5, max_length=120)
    canal: str = "api"


class Solicitud(SolicitudEntrada):
    id_solicitud: str
    estado: str
    fecha_creacion: datetime


class Area(BaseModel):
    id_area: int
    nombre: str
    sede: str
    responsable: str | None = None


class Usuario(BaseModel):
    id_usuario: int
    correo: str
    nombre: str
    id_area: int
    activo: bool


AREAS_SEED: dict[int, Area] = {
    a.id_area: a
    for a in (
        Area(id_area=1, nombre="Aplicaciones", sede="Sede Principal", responsable="Coordinación de Aplicaciones"),
        Area(id_area=2, nombre="Infraestructura", sede="Sede Principal", responsable="Coordinación de Infraestructura"),
        Area(id_area=3, nombre="Talento Humano", sede="Sede Principal", responsable="Jefatura de Talento Humano"),
        Area(id_area=4, nombre="Contabilidad", sede="Sede Principal", responsable="Jefatura Contable"),
        Area(id_area=5, nombre="Compras", sede="Sede Norte", responsable="Jefatura de Compras"),
        Area(id_area=6, nombre="Comercial", sede="Sede Norte", responsable="Dirección Comercial"),
        Area(id_area=7, nombre="Operaciones", sede="Bodega Sur", responsable="Jefatura de Operaciones"),
        Area(id_area=8, nombre="Calidad", sede="Sede Principal", responsable="Coordinación de Calidad"),
    )
}

USUARIOS_SEED: dict[int, Usuario] = {
    u.id_usuario: u
    for u in (
        Usuario(id_usuario=1, correo="usuario001@lafortuna.com.co", nombre="Usuario Demo 001", id_area=5, activo=True),
        Usuario(id_usuario=2, correo="usuario002@lafortuna.com.co", nombre="Usuario Demo 002", id_area=5, activo=False),
        Usuario(id_usuario=3, correo="usuario003@lafortuna.com.co", nombre="Usuario Demo 003", id_area=8, activo=True),
        Usuario(id_usuario=4, correo="usuario004@lafortuna.com.co", nombre="Usuario Demo 004", id_area=3, activo=True),
        Usuario(id_usuario=5, correo="usuario005@lafortuna.com.co", nombre="Usuario Demo 005", id_area=3, activo=True),
        Usuario(id_usuario=6, correo="usuario006@lafortuna.com.co", nombre="Usuario Demo 006", id_area=5, activo=True),
        Usuario(id_usuario=7, correo="usuario007@lafortuna.com.co", nombre="Usuario Demo 007", id_area=2, activo=False),
        Usuario(id_usuario=8, correo="usuario008@lafortuna.com.co", nombre="Usuario Demo 008", id_area=6, activo=True),
        Usuario(id_usuario=9, correo="usuario009@lafortuna.com.co", nombre="Usuario Demo 009", id_area=7, activo=True),
        Usuario(id_usuario=10, correo="usuario010@lafortuna.com.co", nombre="Usuario Demo 010", id_area=4, activo=True),
        Usuario(id_usuario=11, correo="usuario011@lafortuna.com.co", nombre="Usuario Demo 011", id_area=7, activo=True),
        Usuario(id_usuario=12, correo="usuario012@lafortuna.com.co", nombre="Usuario Demo 012", id_area=5, activo=True),
        Usuario(id_usuario=13, correo="usuario013@lafortuna.com.co", nombre="Usuario Demo 013", id_area=4, activo=True),
        Usuario(id_usuario=14, correo="usuario014@lafortuna.com.co", nombre="Usuario Demo 014", id_area=2, activo=True),
        Usuario(id_usuario=15, correo="usuario015@lafortuna.com.co", nombre="Usuario Demo 015", id_area=4, activo=True),
        Usuario(id_usuario=16, correo="usuario016@lafortuna.com.co", nombre="Usuario Demo 016", id_area=3, activo=True),
        Usuario(id_usuario=17, correo="usuario017@lafortuna.com.co", nombre="Usuario Demo 017", id_area=3, activo=True),
        Usuario(id_usuario=18, correo="usuario018@lafortuna.com.co", nombre="Usuario Demo 018", id_area=5, activo=True),
        Usuario(id_usuario=19, correo="usuario019@lafortuna.com.co", nombre="Usuario Demo 019", id_area=3, activo=True),
        Usuario(id_usuario=20, correo="usuario020@lafortuna.com.co", nombre="Usuario Demo 020", id_area=2, activo=False),
        Usuario(id_usuario=21, correo="usuario021@lafortuna.com.co", nombre="Usuario Demo 021", id_area=5, activo=True),
        Usuario(id_usuario=22, correo="usuario022@lafortuna.com.co", nombre="Usuario Demo 022", id_area=7, activo=True),
        Usuario(id_usuario=23, correo="usuario023@lafortuna.com.co", nombre="Usuario Demo 023", id_area=7, activo=False),
        Usuario(id_usuario=24, correo="usuario024@lafortuna.com.co", nombre="Usuario Demo 024", id_area=6, activo=False),
        Usuario(id_usuario=25, correo="usuario025@lafortuna.com.co", nombre="Usuario Demo 025", id_area=4, activo=True),
        Usuario(id_usuario=26, correo="usuario026@lafortuna.com.co", nombre="Usuario Demo 026", id_area=1, activo=True),
        Usuario(id_usuario=27, correo="usuario027@lafortuna.com.co", nombre="Usuario Demo 027", id_area=6, activo=True),
        Usuario(id_usuario=28, correo="usuario028@lafortuna.com.co", nombre="Usuario Demo 028", id_area=1, activo=True),
        Usuario(id_usuario=29, correo="usuario029@lafortuna.com.co", nombre="Usuario Demo 029", id_area=3, activo=True),
        Usuario(id_usuario=30, correo="usuario030@lafortuna.com.co", nombre="Usuario Demo 030", id_area=8, activo=True),
        Usuario(id_usuario=31, correo="usuario031@lafortuna.com.co", nombre="Usuario Demo 031", id_area=4, activo=True),
        Usuario(id_usuario=32, correo="usuario032@lafortuna.com.co", nombre="Usuario Demo 032", id_area=5, activo=True),
        Usuario(id_usuario=33, correo="usuario033@lafortuna.com.co", nombre="Usuario Demo 033", id_area=4, activo=True),
        Usuario(id_usuario=34, correo="usuario034@lafortuna.com.co", nombre="Usuario Demo 034", id_area=8, activo=True),
        Usuario(id_usuario=35, correo="usuario035@lafortuna.com.co", nombre="Usuario Demo 035", id_area=4, activo=True),
        Usuario(id_usuario=36, correo="usuario036@lafortuna.com.co", nombre="Usuario Demo 036", id_area=6, activo=True),
        Usuario(id_usuario=37, correo="usuario037@lafortuna.com.co", nombre="Usuario Demo 037", id_area=1, activo=True),
        Usuario(id_usuario=38, correo="usuario038@lafortuna.com.co", nombre="Usuario Demo 038", id_area=1, activo=True),
        Usuario(id_usuario=39, correo="usuario039@lafortuna.com.co", nombre="Usuario Demo 039", id_area=6, activo=True),
        Usuario(id_usuario=40, correo="usuario040@lafortuna.com.co", nombre="Usuario Demo 040", id_area=8, activo=True),
    )
}
