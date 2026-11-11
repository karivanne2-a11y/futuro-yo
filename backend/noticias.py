"""Titulares de economia y bolsa desde fuentes RSS publicas.

Solo se muestran titulo, fuente, fecha y enlace a la nota original.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import requests

FUENTES = [
    ("Gestión", "Perú", "https://gestion.pe/arc/outboundfeeds/rss/category/economia/?outputType=xml"),
    ("El Comercio", "Perú", "https://elcomercio.pe/arc/outboundfeeds/rss/category/economia/?outputType=xml"),
    ("Andina", "Perú", "https://andina.pe/agencia/rss/3.xml"),
    ("CNBC Markets", "Internacional", "https://www.cnbc.com/id/15839069/device/rss/rss.html"),
    ("MarketWatch", "Internacional", "https://feeds.content.dowjones.io/public/rss/mw_topstories"),
    ("Investing.com", "Internacional", "https://www.investing.com/rss/news_25.rss"),
]
MERCADO = re.compile(
    r"bolsa|bvl|acci[oó]n|mercado|d[oó]lar|tipo de cambio|cobre|oro|bcrp|tasa|inflaci|inversi|bono|afp|"
    r"stock|market|shares|fed|wall street|s&p|nasdaq|dow|treasur|yield|earnings|oil|gold|copper",
    re.IGNORECASE,
)
TAMANO_MAXIMO = 4_000_000


@dataclass
class Noticia:
    titulo: str
    enlace: str
    fuente: str
    region: str
    fecha: datetime | None

    @property
    def de_mercado(self) -> bool:
        return bool(MERCADO.search(self.titulo))


def _fecha(texto: str | None) -> datetime | None:
    if not texto:
        return None
    try:
        f = parsedate_to_datetime(texto.strip())
    except (TypeError, ValueError):
        try:
            f = datetime.fromisoformat(texto.strip().replace("Z", "+00:00"))
        except ValueError:
            return None
    return f if f.tzinfo else f.replace(tzinfo=timezone.utc)


def _texto(nodo, nombre: str) -> str:
    hijo = nodo.find(nombre)
    return (hijo.text or "").strip() if hijo is not None and hijo.text else ""


def parsear(xml: bytes, fuente: str, region: str) -> list[Noticia]:
    """Lee RSS 2.0 o Atom. Descarta enlaces que no sean http o https."""
    raiz = ET.fromstring(xml)
    noticias = []
    atom = "{http://www.w3.org/2005/Atom}"
    items = raiz.iter("item")
    for item in items:
        titulo, enlace = _texto(item, "title"), _texto(item, "link")
        if titulo and enlace.startswith(("http://", "https://")):
            noticias.append(Noticia(titulo, enlace, fuente, region, _fecha(_texto(item, "pubDate"))))
    if not noticias:
        for entrada in raiz.iter(f"{atom}entry"):
            titulo = _texto(entrada, f"{atom}title")
            link = entrada.find(f"{atom}link")
            enlace = link.get("href", "") if link is not None else ""
            if titulo and enlace.startswith(("http://", "https://")):
                fecha = _texto(entrada, f"{atom}updated") or _texto(entrada, f"{atom}published")
                noticias.append(Noticia(titulo, enlace, fuente, region, _fecha(fecha)))
    return noticias


def _descargar_una(fuente: tuple[str, str, str], timeout: float) -> list[Noticia]:
    nombre, region, url = fuente
    r = requests.get(url, timeout=timeout, headers={"User-Agent": "FuturoYo/1.0 (prototipo educativo)"})
    r.raise_for_status()
    if len(r.content) > TAMANO_MAXIMO:
        raise ValueError("Respuesta demasiado grande")
    return parsear(r.content, nombre, region)


def descargar(fuentes=FUENTES, timeout: float = 6.0) -> tuple[list[Noticia], list[str]]:
    """Consulta todas las fuentes en paralelo. Devuelve noticias y fuentes que fallaron."""
    noticias, fallidas = [], []
    with ThreadPoolExecutor(max_workers=6) as pool:
        futuros = {pool.submit(_descargar_una, f, timeout): f[0] for f in fuentes}
        for futuro, nombre in futuros.items():
            try:
                noticias.extend(futuro.result())
            except Exception:
                fallidas.append(nombre)
    minimo = datetime.min.replace(tzinfo=timezone.utc)
    noticias.sort(key=lambda n: n.fecha or minimo, reverse=True)
    return noticias, fallidas


def hace_cuanto(fecha: datetime | None, ahora: datetime | None = None) -> str:
    if fecha is None:
        return ""
    ahora = ahora or datetime.now(timezone.utc)
    minutos = int((ahora - fecha).total_seconds() // 60)
    if minutos < 1:
        return "ahora"
    if minutos < 60:
        return f"hace {minutos} min"
    if minutos < 60 * 24:
        return f"hace {minutos // 60} h"
    return f"hace {minutos // (60 * 24)} d"
