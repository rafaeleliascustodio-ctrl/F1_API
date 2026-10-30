"""
Repository de pilotos: todas as consultas ao banco da tabela `drivers`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.driver import Driver
from app.schemas.driver import DriverCreate, DriverUpdate


def list_drivers(db: Session, skip: int = 0, limit: int = 100) -> list[Driver]:
    """Lista pilotos, ordenados por sobrenome. skip/limit fazem paginação simples."""
    stmt = select(Driver).order_by(Driver.last_name, Driver.first_name).offset(skip).limit(limit)
    # scalars() devolve diretamente os objetos Driver (e não tuplas de colunas).
    return list(db.scalars(stmt).all())


def get_driver(db: Session, driver_id: int) -> Driver | None:
    """Busca um piloto pelo id. Devolve None se não existir."""
    # db.get() é o jeito mais direto de buscar pela chave primária.
    return db.get(Driver, driver_id)


def get_driver_by_acronym(db: Session, acronym: str) -> Driver | None:
    """Busca um piloto pela sigla (ex.: HAM). Útil para evitar duplicatas."""
    stmt = select(Driver).where(Driver.acronym == acronym)
    # scalar_one_or_none(): devolve o objeto, ou None se não houver linha.
    return db.scalars(stmt).one_or_none()


def create_driver(db: Session, data: DriverCreate) -> Driver:
    """Insere um novo piloto e devolve o objeto já com o id gerado."""
    # model_dump() converte o schema em dicionário; ** desempacota em argumentos.
    driver = Driver(**data.model_dump())
    db.add(driver)
    db.commit()
    # refresh() recarrega o objeto do banco, trazendo o id gerado.
    db.refresh(driver)
    return driver


def update_driver(db: Session, driver: Driver, data: DriverUpdate) -> Driver:
    """Atualiza apenas os campos que o cliente enviou."""
    # exclude_unset=True: só inclui campos realmente enviados no PATCH.
    # Assim, "não enviou" não apaga o valor atual.
    changes = data.model_dump(exclude_unset=True)
    for field, value in changes.items():
        setattr(driver, field, value)
    db.commit()
    db.refresh(driver)
    return driver


def delete_driver(db: Session, driver: Driver) -> None:
    """Apaga um piloto."""
    db.delete(driver)
    db.commit()