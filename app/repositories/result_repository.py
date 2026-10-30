"""
Repository de resultados: todas as consultas ao banco da tabela `results`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.result import Result
from app.schemas.result import ResultCreate, ResultUpdate


def list_results(db: Session, skip: int = 0, limit: int = 100) -> list[Result]:
    """Lista resultados ordenados por corrida e posição final, com paginação."""
    stmt = (
        select(Result)
        .order_by(Result.race_id.desc(), Result.position)
        .offset(skip)
        .limit(limit)
    )
    return list(db.scalars(stmt).all())


def get_result(db: Session, result_id: int) -> Result | None:
    """Busca um resultado pelo id. Devolve None se não existir."""
    return db.get(Result, result_id)


def get_result_by_race_driver(db: Session, race_id: int, driver_id: int) -> Result | None:
    """Busca o resultado de um piloto em uma corrida (combinação única)."""
    stmt = select(Result).where(Result.race_id == race_id, Result.driver_id == driver_id)
    return db.scalars(stmt).one_or_none()


def create_result(db: Session, data: ResultCreate) -> Result:
    """Insere um novo resultado e devolve o objeto já com o id gerado."""
    result = Result(**data.model_dump())
    db.add(result)
    db.commit()
    db.refresh(result)
    return result


def update_result(db: Session, result: Result, data: ResultUpdate) -> Result:
    """Atualiza apenas os campos enviados no PATCH."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(result, field, value)
    db.commit()
    db.refresh(result)
    return result


def delete_result(db: Session, result: Result) -> None:
    """Apaga um resultado."""
    db.delete(result)
    db.commit()