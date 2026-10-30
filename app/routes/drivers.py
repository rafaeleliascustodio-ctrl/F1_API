"""
Rotas (endpoints REST) de pilotos.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.repositories import driver_repository as repo
from app.schemas.driver import DriverCreate, DriverResponse, DriverUpdate

# APIRouter agrupa as rotas de pilotos. Todas começam com /drivers.
router = APIRouter(prefix="/drivers", tags=["Pilotos"])


@router.get("", response_model=list[DriverResponse])
def list_drivers(
    # Query(...) define e valida os parâmetros da URL: /drivers?skip=0&limit=20
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
):
    """Lista pilotos, com paginação simples."""
    return repo.list_drivers(db, skip=skip, limit=limit)


@router.get("/{driver_id}", response_model=DriverResponse)
def get_driver(driver_id: int, db: Session = Depends(get_db)):
    """Busca um piloto pelo id."""
    driver = repo.get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Piloto não encontrado.")
    return driver


@router.post("", response_model=DriverResponse, status_code=status.HTTP_201_CREATED)
def create_driver(data: DriverCreate, db: Session = Depends(get_db)):
    """Cria um piloto. Devolve 409 se a sigla já existir."""
    # Checagem antecipada: dá uma mensagem clara ao cliente.
    if repo.get_driver_by_acronym(db, data.acronym):
        raise HTTPException(status_code=409, detail="Já existe um piloto com essa sigla.")
    try:
        return repo.create_driver(db, data)
    except IntegrityError:
        # Rede de segurança (ex.: duas requisições simultâneas com a mesma sigla).
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um piloto com essa sigla.")


@router.patch("/{driver_id}", response_model=DriverResponse)
def update_driver(driver_id: int, data: DriverUpdate, db: Session = Depends(get_db)):
    """Atualiza parcialmente um piloto."""
    driver = repo.get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Piloto não encontrado.")

    # Se a sigla está mudando, confirma que não pertence a outro piloto.
    if data.acronym is not None and data.acronym != driver.acronym:
        if repo.get_driver_by_acronym(db, data.acronym):
            raise HTTPException(status_code=409, detail="Já existe um piloto com essa sigla.")

    try:
        return repo.update_driver(db, driver, data)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="Já existe um piloto com essa sigla.")


@router.delete("/{driver_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_driver(driver_id: int, db: Session = Depends(get_db)):
    """Apaga um piloto. Devolve 409 se ele tiver resultados vinculados."""
    driver = repo.get_driver(db, driver_id)
    if driver is None:
        raise HTTPException(status_code=404, detail="Piloto não encontrado.")
    try:
        repo.delete_driver(db, driver)
    except IntegrityError:
        # A chave estrangeira em `results` impede apagar quem tem resultados.
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Não é possível apagar: o piloto possui resultados vinculados.",
        )
    return Response(status_code=status.HTTP_204_NO_CONTENT)