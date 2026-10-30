"""
Rotas (endpoints REST) de circuitos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories import circuit_repository as repo
from app.schemas.circuit import CircuitCreate, CircuitResponse, CircuitUpdate

router = APIRouter(prefix="/circuits", tags=["Circuitos"])


@router.get("", response_model=list[CircuitResponse])
def list_circuits(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista circuitos, com paginação simples."""
    return repo.list_circuits(db, skip=skip, limit=limit)


@router.get("/{circuit_id}", response_model=CircuitResponse)
def get_circuit(circuit_id: int, db: Session = Depends(get_db)):
    """Busca um circuito pelo id."""
    circuit = repo.get_circuit(db, circuit_id)
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuito não encontrado.")
    return circuit


@router.post("", response_model=CircuitResponse, status_code=status.HTTP_201_CREATED)
def create_circuit(data: CircuitCreate, db: Session = Depends(get_db)):
    """Cria um circuito. Devolve 409 se o nome já existir."""
    if repo.get_circuit_by_name(db, data.name):
        raise HTTPException(status_code=409, detail="Já existe um circuito com esse nome.")
    try:
        return repo.create_circuit(db, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um circuito com esse nome.")


@router.patch("/{circuit_id}", response_model=CircuitResponse)
def update_circuit(circuit_id: int, data: CircuitUpdate, db: Session = Depends(get_db)):
    """Atualiza parcialmente um circuito."""
    circuit = repo.get_circuit(db, circuit_id)
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuito não encontrado.")

    if data.name is not None and data.name != circuit.name:
        if repo.get_circuit_by_name(db, data.name):
            raise HTTPException(status_code=409, detail="Já existe um circuito com esse nome.")

    try:
        return repo.update_circuit(db, circuit, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um circuito com esse nome.")


@router.delete("/{circuit_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_circuit(circuit_id: int, db: Session = Depends(get_db)):
    """Apaga um circuito. Devolve 409 se ele tiver corridas vinculadas."""
    circuit = repo.get_circuit(db, circuit_id)
    if circuit is None:
        raise HTTPException(status_code=404, detail="Circuito não encontrado.")
    try:
        repo.delete_circuit(db, circuit)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível apagar: o circuito possui corridas vinculadas.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)