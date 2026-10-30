"""
Repository de circuitos: todas as consultas ao banco da tabela `circuits`.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.circuit import Circuit
from app.schemas.circuit import CircuitCreate, CircuitUpdate


def list_circuits(db: Session, skip: int = 0, limit: int = 100) -> list[Circuit]:
    """Lista circuitos ordenados por nome, com paginação simples."""
    stmt = select(Circuit).order_by(Circuit.name).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_circuit(db: Session, circuit_id: int) -> Circuit | None:
    """Busca um circuito pelo id. Devolve None se não existir."""
    return db.get(Circuit, circuit_id)


def get_circuit_by_name(db: Session, name: str) -> Circuit | None:
    """Busca um circuito pelo nome (único)."""
    stmt = select(Circuit).where(Circuit.name == name)
    return db.scalars(stmt).one_or_none()


def create_circuit(db: Session, data: CircuitCreate) -> Circuit:
    """Insere um novo circuito e devolve o objeto já com o id gerado."""
    circuit = Circuit(**data.model_dump())
    db.add(circuit)
    db.commit()
    db.refresh(circuit)
    return circuit


def update_circuit(db: Session, circuit: Circuit, data: CircuitUpdate) -> Circuit:
    """Atualiza apenas os campos enviados no PATCH."""
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(circuit, field, value)
    db.commit()
    db.refresh(circuit)
    return circuit


def delete_circuit(db: Session, circuit: Circuit) -> None:
    """Apaga um circuito."""
    db.delete(circuit)
    db.commit()