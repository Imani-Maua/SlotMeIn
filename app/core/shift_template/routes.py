from fastapi import APIRouter, Depends, Body
from sqlalchemy.orm import Session
from typing import Annotated
from datetime import time

from app.database.session import session
from app.core.shift_template.schema import TemplateIn, TemplateUpdate, TemplateOut
from app.core.shift_template.services.service import TemplateService, get_template, get_all_templates


shift_templates = APIRouter(tags=["Shift Templates"])


@shift_templates.post("/create", response_model=TemplateOut)
def create_template(db: Annotated[Session, Depends(session)],
                      data: Annotated[TemplateIn, Body()]
                     
                      ):
    shift_template = TemplateService().create_template(db=db, data=data)
    return shift_template

@shift_templates.put("/update/{template_id}", response_model=TemplateOut)
def update_template(db: Annotated[Session,  Depends(session)],
                              template_id: int,
                              update_data: Annotated[TemplateUpdate, Body()]
                           
                                ):
    updated_template = TemplateService().update_template(db=db, data=update_data, template_id=template_id)
    return updated_template

@shift_templates.delete("/delete/{template_id}", status_code=204, response_model=None)
def delete_template(db: Annotated[Session, Depends(session)],
                              template_id: int
                          
                              ):
    TemplateService().delete_template(db=db, template_id=template_id)

@shift_templates.get("/retrieve_template/{template_id}" , response_model=TemplateOut)
def retrieve_template(db:Annotated[Session, Depends(session)], template_id: int):
    return get_template(db=db, id=template_id)


@shift_templates.get("/retrieve_all_templates", response_model=list[TemplateOut])
def retrieve_templates(db: Annotated[Session, Depends(session)],
                    shift_name: str | None = None,
                    shift_start: time | None = None,
                    shift_end: time | None = None):
    
    return get_all_templates(db=db, 
                             shift_name=shift_name, 
                             shift_start=shift_start, 
                             shift_end=shift_end)



